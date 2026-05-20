import os
import re
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.prompts import PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rag.prompts import SYSTEM_PROMPT

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

_index = None


GREETINGS = {"hi", "hey", "hello", "yo", "sup", "howdy", "hiya", "good morning", "good evening", "good afternoon"}

GENERAL_KEYWORDS = {"what is", "who is", "define", "meaning of", "tell me about"}

SHORT_TRIGGERS = {"explain briefly", "in one line", "summarize", "tldr", "short answer", "briefly"}
LONG_TRIGGERS = {"explain in detail", "elaborate", "in depth", "detailed explanation", "comprehensive", "step by step"}


def classify_query(question: str) -> dict:
    """
    Classify the query to determine:
    - query_type: greeting | general | algorithm
    - num_predict: token budget for response
    - top_k: number of chunks to retrieve
    """
    q = question.lower().strip().rstrip("?!.")

    # Greeting
    if q in GREETINGS or any(q.startswith(g) for g in GREETINGS):
        return {"query_type": "greeting", "num_predict": 60, "top_k": 1}

    # Explicit length hints from user
    if any(t in q for t in SHORT_TRIGGERS):
        base_tokens = 150
    elif any(t in q for t in LONG_TRIGGERS):
        base_tokens = 600
    else:
        base_tokens = 512

    # Algorithm-domain keywords — use RAG
    algo_keywords = [
        "algorithm", "complexity", "big o", "sorting", "searching", "binary search",
        "tree", "graph", "heap", "queue", "stack", "array", "linked list",
        "recursion", "dynamic programming", "greedy", "hash", "bfs", "dfs",
        "traversal", "insertion", "deletion", "node", "edge", "vertex", "path",
        "time complexity", "space complexity", "data structure", "merge sort",
        "quick sort", "bubble sort", "dijkstra", "pri   m", "kruskal", "mst",
    ]

    is_algo = any(kw in q for kw in algo_keywords)

    return {
        "query_type": "algorithm" if is_algo else "general",
        "num_predict": base_tokens,
        "top_k": 4 if is_algo else 2,
    }


def get_llm(num_predict: int) -> Ollama:
    return Ollama(
        model="llama3.2",
        request_timeout=120.0,
        additional_kwargs={"num_predict": num_predict}
    )


def get_index():
    global _index
    if _index is not None:
        return _index

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("docbot")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    _index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    return _index


def query(question: str) -> str:
    classification = classify_query(question)
    query_type = classification["query_type"]
    num_predict = classification["num_predict"]
    top_k = classification["top_k"]

    llm = get_llm(num_predict)
    Settings.llm = llm

    # Greetings — skip RAG entirely, ask LLM directly
    if query_type == "greeting":
        greeting_prompt = (
            f"You are AlgoAsk, a friendly algorithm assistant. "
            f"The user said: '{question}'. Respond warmly tell them what you can help with."
        )
        response = llm.complete(greeting_prompt)
        return str(response)

    # General or algorithm — use RAG
    index = get_index()
    engine = index.as_query_engine(
        similarity_top_k=top_k,
        text_qa_template=PromptTemplate(SYSTEM_PROMPT),
        llm=llm,
    )
    return str(engine.query(question))
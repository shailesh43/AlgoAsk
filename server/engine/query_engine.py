import os
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.prompts import PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rag.prompts import SYSTEM_PROMPT

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

Settings.llm = Ollama(model="llama3.2", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

_query_engine = None


def get_query_engine():
    global _query_engine
    if _query_engine is not None:
        return _query_engine

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("docbot")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )
    _query_engine = index.as_query_engine(
        similarity_top_k=4,
        text_qa_template=PromptTemplate(SYSTEM_PROMPT),
    )
    return _query_engine


def query(question: str) -> str:
    return str(get_query_engine().query(question))

import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import chromadb

Settings.llm = Ollama(model="llama3.2", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "docs")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")


def ingest_documents():
    print("Loading documents...")
    documents = SimpleDirectoryReader(DOCS_PATH).load_data()

    print(f"Loaded {len(documents)} document chunks. Embedding and storing...")

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("docbot")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    print("Ingestion complete. Vectors stored in ChromaDB.")


if __name__ == "__main__":
    ingest_documents()
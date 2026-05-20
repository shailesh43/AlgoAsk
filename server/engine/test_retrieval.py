import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_or_create_collection("docbot")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

retriever = index.as_retriever(similarity_top_k=4)
nodes = retriever.retrieve("what is binary search")

for i, node in enumerate(nodes):
    print(f"\n--- Chunk {i+1} ---")
    print(node.text[:300])
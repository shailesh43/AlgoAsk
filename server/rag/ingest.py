import os
import chromadb
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

Settings.llm = Ollama(model="llama3.2", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "docs")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")


def is_text_based(text: str, threshold: float = 0.1) -> bool:
    """Check if extracted text is meaningful or just garbage from a scanned PDF."""
    if not text or len(text.strip()) == 0:
        return False
    words = text.split()
    if len(words) == 0:
        return False
    avg_word_len = sum(len(w) for w in words) / len(words)
    return avg_word_len < 20 and len(words) > 10


def extract_with_ocr(pdf_path: str) -> str:
    """Fallback OCR extraction using pytesseract for scanned PDFs."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
        print(f"  Running OCR on: {os.path.basename(pdf_path)}")
        images = convert_from_path(pdf_path, dpi=200)
        full_text = ""
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            full_text += f"\n--- Page {i + 1} ---\n{text}"
        return full_text
    except ImportError:
        print("  OCR skipped: install pytesseract and pdf2image for scanned PDF support.")
        return ""


def load_documents_with_ocr_fallback():
    """Load PDFs, falling back to OCR for scanned ones."""
    from llama_index.core import Document

    documents = []
    pdf_files = [f for f in os.listdir(DOCS_PATH) if f.endswith(".pdf")]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(DOCS_PATH, pdf_file)
        print(f"Processing: {pdf_file}")

        # Try standard text extraction first
        try:
            docs = SimpleDirectoryReader(input_files=[pdf_path]).load_data()
            combined_text = " ".join(d.text for d in docs)

            if is_text_based(combined_text):
                print(f"  Text-based PDF — extracted {len(combined_text)} characters")
                documents.extend(docs)
            else:
                print(f"  Scanned PDF detected — switching to OCR")
                ocr_text = extract_with_ocr(pdf_path)
                if ocr_text:
                    documents.append(Document(
                        text=ocr_text,
                        metadata={"file_name": pdf_file, "source": "ocr"}
                    ))
        except Exception as e:
            print(f"  Failed to process {pdf_file}: {e}")

    return documents


def ingest_documents():
    print("Loading documents...\n")
    documents = load_documents_with_ocr_fallback()
    print(f"\nLoaded {len(documents)} document pages total.")

    # Optimized chunking: larger chunks preserve more context per concept
    splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=64,
    )
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Split into {len(nodes)} chunks for embedding.")

    # Wipe existing collection to avoid stale/duplicate vectors
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        chroma_client.delete_collection("docbot")
        print("Cleared existing ChromaDB collection.")
    except Exception:
        pass

    chroma_collection = chroma_client.get_or_create_collection("docbot")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(nodes, storage_context=storage_context)

    print("Ingestion complete. Vectors stored in ChromaDB.")


if __name__ == "__main__":
    ingest_documents()
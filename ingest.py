from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from config import DATA_DIR, VECTORSTORE_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


def ingest_data() -> bool:
    """Build FAISS vectorstore from PDFs in DATA_DIR. Returns True on success."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = [f for f in DATA_DIR.iterdir() if f.suffix.lower() == ".pdf"]
    if not pdf_files:
        print(f"No PDF files found in '{DATA_DIR}' directory.")
        return False

    documents = []
    for file in pdf_files:
        print(f"Processing document: {file.name}...")
        loader = PyMuPDFLoader(str(file))
        documents.extend(loader.load())

    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)

    print("Generating embeddings. This may take some time depending on your CPU...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    vectorstore.save_local(str(VECTORSTORE_DIR))
    print(f"Data ingestion complete. Vector store saved to '{VECTORSTORE_DIR}'.")
    return True

if __name__ == "__main__":
    ingest_data()
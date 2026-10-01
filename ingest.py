import argparse
import glob
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pdf_loader import load_pdf_pages

# Readable names stored on every chunk so answers can cite "which document, which page".
DOC_NAMES = {
    "academic_rules_regulations_2024.pdf": "Academic Rules and Regulations 2024",
    "dot_policy_2025_26.pdf": "DoT Policy 2025-26",
    "attendance_policy.pdf": "Attendance Monitoring Policy",
    "code_of_ethics.pdf": "Code of Ethics and Conduct",
    "plagiarism_policy_2016.pdf": "Plagiarism Policy 2016",
}

# PDFs whose built-in text layer is badly garbled (e.g. "Plagiadsm", "ptagia sm") — read these by OCR instead.
FORCE_OCR = {"plagiarism_policy_2016.pdf"}


def ingest(chunk_size=1000, chunk_overlap=150, persist_directory="chroma_db", data_dir="data"):
    # Chroma.from_documents adds to an existing store, so re-running would silently duplicate every chunk.
    if os.path.isdir(persist_directory) and os.listdir(persist_directory):
        raise SystemExit(f"{persist_directory}/ already has data — move or delete it first (or pass --persist-directory).")

    # 1. Load every PDF — one Document object per page (scanned pages are OCR'd)
    documents = []
    for pdf_path in sorted(glob.glob(os.path.join(data_dir, "*.pdf"))):
        filename = os.path.basename(pdf_path)
        pages = load_pdf_pages(pdf_path, force_ocr=filename in FORCE_OCR)
        for page in pages:
            page.metadata["doc_name"] = DOC_NAMES.get(filename, os.path.splitext(filename)[0])
        ocr_pages = sum(p.metadata["ocr"] for p in pages)
        print(f"Loaded {len(pages)} pages from {filename} ({ocr_pages} via OCR)")
        documents.extend(pages)

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})")

    # 3. Embed each chunk and store it in a local vector database
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    print(f"Stored in {persist_directory}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=150)
    parser.add_argument("--persist-directory", default="chroma_db")
    args = parser.parse_args()
    ingest(args.chunk_size, args.chunk_overlap, args.persist_directory)

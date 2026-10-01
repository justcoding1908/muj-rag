FROM python:3.14-slim

WORKDIR /app

# opencv (a rapidocr dependency) needs these at runtime even though we won't actually
# call OCR during the build — the import happens, so the shared libs must be present.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# sentence-transformers (a HuggingFaceEmbeddings dependency) pulls in torch, and pip's
# default wheel for it is the full CUDA build — 500MB+ plus another 500MB+ of Nvidia
# CUDA/cuDNN libraries, none of which this CPU-only container can use. Install the much
# smaller CPU-only build first so the later install finds torch already satisfied.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the vector database at image-build time, not at container startup. data/ (the
# PDFs) and ocr_cache/ (cached OCR text for the scanned ones) are both committed, so
# this needs no OCR and no external calls — just embedding, which happens once per image
# build rather than on every container start.
RUN python ingest.py

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]

import json
import os
import re
from langchain_community.document_loaders import PyPDFLoader

# A page with fewer characters than this is treated as a scanned image with no real text.
MIN_TEXT_CHARS = 50
OCR_SCALE = 2.5  # render resolution for OCR; 2.5 read the DoT policy cleanly
OCR_CACHE_DIR = "ocr_cache"
# Printed footers like "Page 3 of 10" sit one behind the real PDF page in some documents, and the
# model was citing them instead of the page label we give it — drop them from the text.
PRINTED_PAGE_FOOTER = re.compile(r"^[ \t]*Page\s+\d+\s+of\s+\d+[ \t]*\n?", re.IGNORECASE | re.MULTILINE)

_engine = None


def _ocr_engine():
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR
        _engine = RapidOCR(params={"Global.log_level": "warning"})
    return _engine


def _ocr_page(pdf, page_index):
    image = pdf[page_index].render(scale=OCR_SCALE).to_numpy()
    result = _ocr_engine()(image)
    return "\n".join(result.txts or [])


def _load_cache(pdf_path):
    cache_path = os.path.join(OCR_CACHE_DIR, os.path.splitext(os.path.basename(pdf_path))[0] + ".json")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        # OCR results belong to one exact file — ignore them if the PDF has changed.
        if cache.get("pdf_size") == os.path.getsize(pdf_path):
            return cache_path, cache
    return cache_path, {"pdf_size": os.path.getsize(pdf_path), "pages": {}}


def load_pdf_pages(pdf_path, force_ocr=False):
    """One Document per page. Pages with no extractable text are OCR'd (and cached).

    force_ocr=True OCRs every page even if it has a text layer — for PDFs whose built-in text is garbled.
    """
    documents = PyPDFLoader(pdf_path).load()
    cache_path, cache = _load_cache(pdf_path)
    pdf = None

    for doc in documents:
        page_index = doc.metadata["page"]
        doc.metadata["ocr"] = False
        if not force_ocr and len(doc.page_content.strip()) >= MIN_TEXT_CHARS:
            continue

        key = str(page_index)
        if key not in cache["pages"]:
            if pdf is None:
                import pypdfium2
                pdf = pypdfium2.PdfDocument(pdf_path)
            print(f"  OCR {os.path.basename(pdf_path)} page {page_index + 1}/{len(documents)} ...", flush=True)
            cache["pages"][key] = _ocr_page(pdf, page_index)
            os.makedirs(OCR_CACHE_DIR, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)

        doc.page_content = cache["pages"][key]
        doc.metadata["ocr"] = True

    for doc in documents:
        doc.page_content = PRINTED_PAGE_FOOTER.sub("", doc.page_content)
    return documents

from typing import List
import logging

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a given PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The extracted text from the PDF.
    """
    try:
        document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += str(page.get_text())
        logging.info(f"Successfully extracted text from {pdf_path}")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""



def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Splits a given text into smaller chunks.

    Args:
        text: The text to be chunked.
        chunk_size: The desired size of each chunk.
        chunk_overlap: The overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks
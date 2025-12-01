from typing import List
from src.config import logger

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
        logger.info(f"Successfully extracted text from {pdf_path}")
        if not text:
            logger.warning(f"Extracted text from {pdf_path} is empty.")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
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
    logger.debug(f"Chunking text with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    if not text:
        logger.warning("No text provided for chunking.")
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    logger.info(f"Text chunked into {len(chunks)} chunks.")
    return chunks
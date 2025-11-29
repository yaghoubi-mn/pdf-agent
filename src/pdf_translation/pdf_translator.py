import logging
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.agent.translator import translate_text
from src.config import UPLOAD_PDF, PROCESSED_PDF





def translate_pdf(target_language: str, input_pdf_path: str, output_pdf_path: str):
    """
    Translates a PDF file to a target language and saves it using reportlab.
    """
    logging.info(f"Starting PDF translation for '{input_pdf_path}'...")
    src_doc = fitz.open(input_pdf_path)
    pages_text = [page.get_text() for page in src_doc]
    translated_pages = []

    for page_num in range(len(pages_text)):
        current_page = pages_text[page_num]
        previous_pages = pages_text[max(0, page_num - 3):page_num]
        next_pages = pages_text[page_num + 1:page_num + 4]
        
        translated_text = translate_text(
            current_page=current_page,
            target_language=target_language,
            previous_pages=previous_pages,
            next_pages=next_pages
        )
        translated_pages.append(translated_text)

    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    for translated_text in translated_pages:
        text_object = c.beginText(40, height - 40)
        text_object.setFont("Times-Roman", 12)
        for line in translated_text.split('\n'):
            text_object.textLine(line)
        c.drawText(text_object)
        c.showPage()

    c.save()
    logging.info(f"Translated PDF saved to '{output_pdf_path}'")
    return True


def translate_pdf_tool(target_language: str):
    return translate_pdf(
        target_language=target_language,
        input_pdf_path=UPLOAD_PDF,
        output_pdf_path=PROCESSED_PDF
    )

# if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    # translator = PdfTranslator(target_language='English')
    # translator.translate_pdf('data/raw_pdfs/test.pdf', 'data/test.pdf')
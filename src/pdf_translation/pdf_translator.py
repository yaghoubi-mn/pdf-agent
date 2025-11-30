import logging
import os
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.agent.translator import translate_text
from src.config import UPLOAD_PDF, PROCESSED_PDF
from src.pdf_translation.utils import get_or_register_font





def translate_pdf(target_language: str, input_pdf_path: str, output_pdf_path: str):
    """
    Translates a PDF file to a target language and saves it using reportlab.
    """
    logging.info(f"Starting PDF translation for '{input_pdf_path}'...")

    doc = fitz.open(input_pdf_path)

    font_cache = {}

    for page_num, page in enumerate(doc):
        logging.info(f"Proccessing page {page_num+1}/{len(doc)} ...")

  
        # for now only get one next page and one previous page
        previous_pages = []
        if page_num > 0:
            previous_pages.append(doc.load_page(page_num).get_text())
        next_pages = []
        if page_num < len(doc) - 1:
            next_pages.append(doc.load_page(page_num).get_text())

        raw_blocks = page.get_text('blocks')
        raw_dict = page.get_text('dict')
        
        text_blocks_payload = []
        mapping = []

        for i, b in enumerate(raw_blocks):
            if b[6] == 0: # type 0 is text, type 1 is image
                text = b[4].strip()
                if text:
                    payload = {'id': i, 'text': text}
                    text_blocks_payload.append(payload)

                    first_span = raw_dict['blocks'][i]["lines"][0]["spans"][0]
                    fontsize = first_span['size']
                    font = first_span['font']
                    color_int = first_span['color']
                    alpha = first_span['alpha']

                    # convert color to RGB format
                    red = ((color_int >> 16) & 0xFF) / 255.0
                    green = ((color_int >> 8) & 0xFF) / 255.0
                    blue = (color_int & 0xFF) / 255.0
                    color = (red, green, blue)
                    mapping.append((i, b, fontsize, color, alpha, font))

        if not text_blocks_payload:
            continue

        translated_map = translate_text(
            blocks=text_blocks_payload,
            target_language=target_language,
            previous_pages=previous_pages,
            next_pages=next_pages
        )
        

        # remove orginal text
        page.add_redact_annot(page.rect)
        page.apply_redactions(images=0, graphics=0)


        for i, orginal_block, fontsize, color, alpha, font in mapping:
            translated_text = translated_map.get(i)

            if translated_text:

                rect = fitz.Rect(orginal_block[:4]) # extract x0, y0, x1, y1

                # usable_font_name = get_or_register_font(doc, page, font, font_cache)

                # insert new text
                try:
                    tries_num = 10
                    for attemp in range(tries_num):
                        result = page.insert_textbox(
                            rect,
                            translated_text,
                            fontname='helv', # TODO: replace with font and check font exist
                            fontsize=fontsize,
                            align=0, # 0=left, 1=center, 2=right (TODO: replace with 2 in RTL languages) 
                            color=color,
                            fill_opacity=alpha,
                        )

                        if result < 0 and attemp == tries_num -1:
                            logging.warning(f"Cannot fix the translated text into the textbox: needed space: {result}")

                        # decrease fontsize until it fit
                        if result < 0:
                            # rect.y1 += abs(result) +3
                            rect.x1 += abs(result)
                            fontsize /= 1.2

                        if rect.y1 > page.rect.y1:
                            rect.y1 = page.rect.y1
                            fontsize -= 1


                except Exception as e:
                    logging.info(f'Could not insert the text block: {type(e)}: {e}')

    
    
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    doc.save(output_pdf_path)

    # c = canvas.Canvas(output_pdf_path, pagesize=letter)
    # width, height = letter
    # for translated_text in translated_pages:
    #     text_object = c.beginText(40, height - 40)
    #     text_object.setFont("Times-Roman", 12)
    #     for line in translated_text.split('\n'):
    #         text_object.textLine(line)
    #     c.drawText(text_object)
    #     c.showPage()

    # c.save()
    logging.info(f"Translated PDF saved to '{output_pdf_path}'")
    return True


def translate_pdf_tool(target_language: str):
    return translate_pdf(
        target_language=target_language,
        input_pdf_path=UPLOAD_PDF,
        output_pdf_path=PROCESSED_PDF
    )

if __name__ == '__main__':
    from dotenv import load_dotenv
    print('load env:', load_dotenv())
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    translate_pdf('German', 'data/uploads/upload.pdf', 'data/test.pdf')
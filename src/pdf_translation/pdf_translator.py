import os
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.agent.translator import translate_text
from src.config import UPLOAD_PDF, PROCESSED_PDF, logger
from src.pdf_translation.utils import get_or_register_font





def translate_pdf(target_language: str, input_pdf_path: str, output_pdf_path: str):
    """
    Translates a PDF file to a target language and saves it using reportlab.
    """
    logger.info(f"Starting PDF translation for '{input_pdf_path}' to '{target_language}'...")
    logger.debug(f"Input PDF: {input_pdf_path}, Output PDF: {output_pdf_path}")

    doc = fitz.open(input_pdf_path)

    font_cache = {}

    for page_num, page in enumerate(doc):
        logger.info(f"Processing page {page_num+1}/{len(doc)} for translation.")

        previous_pages_content = []
        if page_num > 0:
            previous_pages_content.append(doc.load_page(page_num - 1).get_text()) # Adjusted to get actual previous page
        
        next_pages_content = []
        if page_num < len(doc) - 1:
            next_pages_content.append(doc.load_page(page_num + 1).get_text()) # Adjusted to get actual next page

        # Get text blocks and their properties from the current page
        raw_blocks_info = page.get_text('blocks')
        raw_page_dict = page.get_text('dict')
        
        text_blocks_for_translation = []
        block_metadata_mapping = []

        for block_idx, block_data in enumerate(raw_blocks_info):
            if block_data[6] == 0:  # Assuming type 0 is text block
                text_content = block_data[4].strip()
                if text_content:
                    text_blocks_for_translation.append({'id': block_idx, 'text': text_content})
                    
                    # Extract font, size, and color information from the first span of the first line
                    # This relies on the structure of PyMuPDF's 'dict' output for text analysis
                    # More robust parsing might be needed for complex PDFs
                    try:
                        first_line_spans = raw_page_dict['blocks'][block_idx]["lines"][0]["spans"][0]
                        font_size = first_line_spans['size']
                        font_name = first_line_spans['font']
                        color_int = first_line_spans['color']
                        alpha = first_line_spans['alpha']

                        # Convert color integer to RGB tuple (0.0-1.0 range)
                        red = ((color_int >> 16) & 0xFF) / 255.0
                        green = ((color_int >> 8) & 0xFF) / 255.0
                        blue = (color_int & 0xFF) / 255.0
                        color_rgb = (red, green, blue)
                        
                        block_metadata_mapping.append((block_idx, block_data, font_size, color_rgb, alpha, font_name))
                    except IndexError:
                        logger.warning(f"Could not extract span info for block {block_idx} on page {page_num+1}. Skipping font/color preservation.")
                        block_metadata_mapping.append((block_idx, block_data, 12, (0,0,0), 1, 'helv')) # Default if metadata extraction fails

        if not text_blocks_for_translation:
            logger.debug(f"No translatable text blocks found on page {page_num+1}. Skipping translation for this page.")
            continue

        logger.info(f"Translating {len(text_blocks_for_translation)} text blocks on page {page_num+1}.")
        translated_map = translate_text(
            blocks=text_blocks_for_translation,
            target_language=target_language,
            previous_pages=previous_pages_content,
            next_pages=next_pages_content
        )
        if not translated_map:
            logger.warning(f"No translations received for page {page_num+1}. Skipping further processing for this page.")
            continue
        
        # Redact original text before inserting translated text
        try:
            page.add_redact_annot(page.rect)
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_IMAGE_NONE)
            logger.debug(f"Original text redacted on page {page_num+1}.")
        except Exception as e:
            logger.error(f"Error redacting text on page {page_num+1}: {e}")

        for block_idx, original_block_data, font_size, color_rgb, alpha, font_name in block_metadata_mapping:
            translated_text = translated_map.get(block_idx)

            if translated_text:
                rect = fitz.Rect(original_block_data[:4])  # Extract x0, y0, x1, y1
                usable_font_name = get_or_register_font(doc, page, font_name, font_cache) # Use font from original, or register a default

                adjusted_font_size = font_size
                text_insert_successful = False
                
                # Try to insert text, adjusting size/box if necessary
                for attempt in range(10): # Max 10 attempts to fit text
                    try:
                        # Attempt to insert textbox with current parameters
                        # Align can be 0 (left), 1 (center), 2 (right)
                        # For RTL languages, this might need to be 2
                        result = page.insert_textbox(
                            rect,
                            translated_text,
                            fontname=usable_font_name,
                            fontsize=adjusted_font_size,
                            align=0, # Assuming left alignment for now
                            color=color_rgb,
                            fill_opacity=alpha,
                        )

                        if result >= 0: # Text fits
                            text_insert_successful = True
                            logger.debug(f"Successfully inserted translated text for block {block_idx} on page {page_num+1} (attempt {attempt+1}).")
                            break
                        else: # Text overflows (result < 0 indicates needed space)
                            logger.debug(f"Text overflow for block {block_idx} on page {page_num+1}. Needed: {result}. Adjusting font size and rect.")
                            # Adjust font size and/or rectangle to fit text
                            adjusted_font_size *= 0.9 # Reduce font size
                            
                            # Expand the rectangle horizontally if possible, or vertically if needed
                            # This logic might need further refinement based on specific layout requirements
                            current_width = rect.x1 - rect.x0
                            # If text is very long, allow horizontal expansion up to page width or
                            # try to expand vertically more aggressively.
                            # For simplicity, will just decrease font size and try to expand rect.
                            
                            # Simple rectangle expansion (example - could be more sophisticated)
                            rect.x1 = min(rect.x1 - result, page.rect.x1) # Try to extend right boundary if space needed
                            if adjusted_font_size < 5: # Don't go below a certain font size
                                logger.warning(f"Font size for block {block_idx} on page {page_num+1} is too small. Stopping adjustments.")
                                break

                    except Exception as insert_e:
                        logger.error(f"Error inserting textbox for block {block_idx} on page {page_num+1} (attempt {attempt+1}): {insert_e}")
                        break # Stop trying for this block

                if not text_insert_successful:
                    logger.warning(f"Could not fit translated text for block {block_idx} on page {page_num+1} after multiple attempts. Text: '{translated_text[:50]}...'")

        # raw_blocks = page.get_text('blocks')
        # raw_dict = page.get_text('dict')
        
        # text_blocks_payload = []
        # mapping = []

        # for i, b in enumerate(raw_blocks):
        #     if b[6] == 0: # type 0 is text, type 1 is image
        #         text = b[4].strip()
        #         if text:
        #             payload = {'id': i, 'text': text}
        #             text_blocks_payload.append(payload)

        #             first_span = raw_dict['blocks'][i]["lines"][0]["spans"][0]
        #             fontsize = first_span['size']
        #             font = first_span['font']
        #             color_int = first_span['color']
        #             alpha = first_span['alpha']

        #             # convert color to RGB format
        #             red = ((color_int >> 16) & 0xFF) / 255.0
        #             green = ((color_int >> 8) & 0xFF) / 255.0
        #             blue = (color_int & 0xFF) / 255.0
        #             color = (red, green, blue)
        #             mapping.append((i, b, fontsize, color, alpha, font))

        # if not text_blocks_payload:
        #     continue

        # translated_map = translate_text(
        #     blocks=text_blocks_payload,
        #     target_language=target_language,
        #     previous_pages=previous_pages,
        #     next_pages=next_pages
        # )
        

        # # remove orginal text
        # page.add_redact_annot(page.rect)
        # page.apply_redactions(images=0, graphics=0)


        # for i, orginal_block, fontsize, color, alpha, font in mapping:
        #     translated_text = translated_map.get(i)

        #     if translated_text:

        #         rect = fitz.Rect(orginal_block[:4]) # extract x0, y0, x1, y1

        #         # usable_font_name = get_or_register_font(doc, page, font, font_cache)

        #         # insert new text
        #         try:
        #             tries_num = 10
        #             for attemp in range(tries_num):
        #                 result = page.insert_textbox(
        #                     rect,
        #                     translated_text,
        #                     fontname='helv', # TODO: replace with font and check font exist
        #                     fontsize=fontsize,
        #                     align=0, # 0=left, 1=center, 2=right (TODO: replace with 2 in RTL languages) 
        #                     color=color,
        #                     fill_opacity=alpha,
        #                 )

        #                 if result < 0 and attemp == tries_num -1:
        #                     logging.warning(f"Cannot fix the translated text into the textbox: needed space: {result}")

        #                 # decrease fontsize until it fit
        #                 if result < 0:
        #                     # rect.y1 += abs(result) +3
        #                     rect.x1 += abs(result)
        #                     fontsize /= 1.2

        #                 if rect.y1 > page.rect.y1:
        #                     rect.y1 = page.rect.y1
        #                     fontsize -= 1


        #         except Exception as e:
        #             logging.info(f'Could not insert the text block: {type(e)}: {e}')

    
    
    logger.info("Finished processing all pages. Saving translated PDF.")
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    try:
        doc.save(output_pdf_path)
        logger.info(f"Translated PDF saved to '{output_pdf_path}' successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving translated PDF to '{output_pdf_path}': {e}")
        return False


def translate_pdf_tool(target_language: str):
    return translate_pdf(
        target_language=target_language,
        input_pdf_path=UPLOAD_PDF,
        output_pdf_path=PROCESSED_PDF
    )

if __name__ == '__main__':
    from dotenv import load_dotenv
    print('load env:', load_dotenv())
    # Note: genai.configure and logging.basicConfig are handled by src.config and main.py
    # if this script is run as part of the larger application.
    # For standalone testing, you might need to uncomment and configure.
    # import google.generativeai as genai
    # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    # import logging
    # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Running pdf_translator.py in standalone mode for testing.")
    translate_pdf('German', 'data/uploads/upload.pdf', 'data/test.pdf')
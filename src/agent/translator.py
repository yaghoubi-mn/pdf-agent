import os
import time
import json
import google.generativeai as genai

# Configure the generative AI model
# genai.configure(api_key="YOUR_API_KEY")
from src.config import logger

model = genai.GenerativeModel(
    os.getenv("TRANSLATOR_MODEL_NAME", 'gemma-3-27b-it'),
)

SYSTEM_INSTRUCTION="""
        You are a layout-preserving PDF translator.
        I will provide a JSON list of text blocks. each block has an 'id' and 'text'.
        Your task:
        1. Translate the 'text' to the target language.
        2. Return strictly a JSON list of objects with 'id' and 'translation'.
        3. DO NOT change the 'id'.
        4. DO NOT translate technical IDs, numbers, or URLs, unless necessary.
        5. The output must be a valid JSON. Not markdown formatting.
        6. I will also provide you some next and previous pages for better translating. DO NOT translate them, just use them for better translating.
        """

def translate_text(blocks: list[dict], target_language: str, previous_pages: list[str], next_pages: list[str]):
    """

    """
    logger.info(f"Translating {len(blocks)} blocks to {target_language}.")
    
    if not blocks:
        logger.debug("No blocks provided for translation.")
        return {}


    blocks_json = json.dumps(blocks, ensure_ascii=False)


    # Prepare the context for the generative model
    context = f"\nblocks JSON: ```\n{blocks_json}\n```"
    context += f"\n\nPrevious pages:\n ```\n{[f"{page}\n" for page in previous_pages]}```"
    context += f"\nNext pages:\n ```\n{[f"{page}\n" for page in next_pages]}```"

    # Generate a response using the generative model
    for _ in range(10):
        try:
            response = model.generate_content(
                f"SYSTEM INSTRUCTION: {SYSTEM_INSTRUCTION}\nTarget language: {target_language}.\n{context}"
            )

            text_resp = response.text.strip()
            if text_resp.startswith('```json'):
                text_resp = text_resp[7:]
            if text_resp.startswith('```'):
                text_resp = text_resp[3:]
            if text_resp.endswith('```'):
                text_resp = text_resp[:-3]

            translated_list = json.loads(text_resp)

            logger.debug(f'Original blocks: {blocks_json}')
            logger.debug(f'Translated blocks: {text_resp}')
            logger.info("Text blocks translated successfully.")

            return {item['id']: item['translation'] for item in translated_list}
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from translator model: {e}. Raw response: {text_resp}")
            time.sleep(15)
        except Exception as e:
            logger.error(f'An unexpected error occurred during translation: {e}')
            logger.info("Sleeping for 15 seconds before retrying translation...")
            time.sleep(15)


    return {}

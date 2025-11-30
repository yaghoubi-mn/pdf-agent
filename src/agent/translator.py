import json
import logging
import os
import time
import google.generativeai as genai

# Configure the generative AI model
# genai.configure(api_key="YOUR_API_KEY")
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
    
    if not blocks:
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

            logging.info(f'orginal blocks: {blocks_json}')
            logging.info(f'translated blocks: {text_resp}')

            return {item['id']: item['translation'] for item in translated_list}
            
        except Exception as e:
            logging.error(f'error in translating: {e}')
            logging.info("sleeping for 15 seconds ...")
            time.sleep(15)


    return {}

import logging
import time
import google.generativeai as genai
from .rag import generate_embeddings
from src.agent.vector_db import search_vectors

# Configure the generative AI model
# genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel(
    'gemma-3-27b-it',
)

SYSTEM_INSTRUCTION="""You are a text translator.
        Your task is to translate a PDF.
        The user will give you the pdf page by page and you must translate it to the user wanted language.
        I also give you previous PDF pages and next PDF pages so you can translate better (dont translate next and previous pages just translate currcnt page).
        The page is splited to some texts that each one have an id, your ouput MUST be the same format and the ids must be correct.
        only respond with translated text and no other words."""

def translate_text(current_page: str, target_language: str, previous_pages: list[str], next_pages: list[str]):
    """

    """


    # Prepare the context for the generative model
    context = f"\nCurrent page is: ```\n{current_page}\n```"
    context += f"\nPrevious pages:\n ```\n{[f"{page}\n" for page in previous_pages]}```"
    context += f"\nNext pages:\n ```\n{[f"{page}\n" for page in next_pages]}```"

    # Generate a response using the generative model
    for _ in range(10):
        try:
            response = model.generate_content(
                f"SYSTEM INSTRUCTION: {SYSTEM_INSTRUCTION}\nuser prompt: Translate this page to {target_language}.\n{context}"
            )
            break
        except Exception as e:
            logging.error(f'error in translating: {e}')
            logging.info("sleeping for 15 seconds ...")
            time.sleep(15)

    logging.info(f"translating page: {current_page[:100]} \t translated page {response.text[:100]}")

    return response.text

import os
import asyncio
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

from src.agent import config
from src.agent.rag import search_pdf
from src.pdf_translation.pdf_translator import translate_pdf_tool
from src.config import logger


session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
app_name = 'agents'

def create_agent_runner():
    logger.info("Creating PDF assistant agent runner.")
    
    agent = Agent(
        name="pdf_assistant",
        model=Gemini(
            model=os.getenv("AGENT_MODEL_NAME", "gemini-2.5-flash-lite"),
            retry_options=config.retry,
        ),
        description="A agent that answer questions based on PDF",
        tools=[search_pdf, translate_pdf_tool],
        instruction="""
        You are a generic PDF assistant.

        YOUR CAPIBILITIES: 
        1. **Answer Questions**: Answer user questions based on PDF. use `search_pdf` tool to find answers.
        2. **Generate Quizzes**: If requested generate quiz JSON format (see format below).
        3. **Translate PDF**: If requested use `translate_pdf_tool`. It will automatually translate entier pdf and show the pdf to user. you must respond with JSON format (see format below). use this tool only if user requested directly to translate all of the pdf.

        --- QUIZ FORMAT RULES ---
        if user requested for quiz:
            1. search the pdf for requested topic.
            2. output a raw JSON object. do not warp markdown.
            3. DO NOT ask respond with draft quiz, only response with final quiz.
            4. use this EXACT structure:
            {
                "quiz_result": "Done",
                "model_response": "<your-response>",5
                "title": "<quiz-title>",
                "questions": [
                    {
                        "id": <int>,
                        "question": "<question>",
                        "type": "<multiple_choices or open_ended>",
                        "choices": ["options A", "option B", "option C", "option D"],
                        "correct_answer": "<correct-answer>",
                        "difficulty": "<easy or medium or hard>",
                        "source_page": <int>
                    }
                ]
            }

        --- TRANSLATE PDF FORMAT RULES ---
        Output a raw JSON object. do not warp markdown.
        use this EXACT structure:
        {
            "translate_pdf": "Done",
            "model_response": "<your-response>"
        }

        --- GENERAL RULES ---
        - If user question not found in PDF, just say to user i couldn't find your question on pdf.
        - Do not ask user for pdf, use your tools.
             
        """
    )



    return Runner(
        app_name=app_name,
        agent=agent,
        session_service=session_service,
        artifact_service=artifact_service,
    ) 


def init_session(session_id: str, user_id: str):
    logger.info(f"Initializing session for user: {user_id}, session: {session_id}")

    async def _get_or_create():
        logger.debug(f"Attempting to get or create session {session_id} for user {user_id}")
        session = await session_service.get_session(
            session_id=session_id,
            user_id=user_id,
            app_name=app_name
        )
        if not session:
            logger.info(f"Session {session_id} not found, creating a new session.")
            await session_service.create_session(
                session_id=session_id,
                user_id=user_id,
                app_name=app_name
            )
            logger.info(f"Session {session_id} created successfully.")
        else:
            logger.info(f"Session {session_id} retrieved successfully.")

    try:
        asyncio.run(_get_or_create())
    except RuntimeError as e:
        logger.warning(f"RuntimeError during session initialization: {e}. Retrying with existing event loop.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_get_or_create())
    except Exception as e:
        logger.error(f"An unexpected error occurred during session initialization: {e}")


        
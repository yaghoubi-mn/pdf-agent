import asyncio
import logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

from src.agent.schemas import QuizOutput

from src.agent import config
from src.agent.rag import search_pdf, get_pdf_page
from src.pdf_translation.pdf_translator import translate_pdf_tool


session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
app_name = 'agents'

def create_agent_runner():
    

    agent = Agent(
        name="pdf_assistant",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=config.retry,
        ),
        description="A agent that answer questions based on PDF",
        tools=[get_pdf_page, search_pdf, translate_pdf_tool],
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
                # in normal mode don't need to respond with JSON, only respond with plain text.
    )



    return Runner(
        app_name=app_name,
        agent=agent,
        session_service=session_service,
        artifact_service=artifact_service,
    ) 


def init_session(session_id: str, user_id: str):

    async def _get_or_create():
            

    
        session = await session_service.get_session(
            session_id=session_id,
            user_id=user_id,
            app_name=app_name
        )
        if not session:
            logging.info(f"session not found creating a new session.")
            await session_service.create_session(
                session_id=session_id,
                user_id=user_id,
                app_name=app_name
            )

    try:
        asyncio.run(_get_or_create())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_get_or_create())


        
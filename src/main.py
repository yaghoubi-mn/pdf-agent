import json
import os
import tempfile
import uuid

import streamlit as st
from dotenv import load_dotenv
from google.genai import types

from src.agent.core import create_agent_runner, init_session
from src.agent.schemas import QuizOutput
from src.agent.rag import setup_rag_pipeline
from src.agent.vector_db import get_all_collection_data, get_qdrant_client
from src.ui.components import display_pdf_translation, render_quiz
from src import config
from src.config import logger




def main():
    logger.info("PDF Agent application started.")
    load_dotenv()

    st.set_page_config(page_title="PDF Agent", layout="wide")

    st.title("PDF Agent")

    if not config.qdrant_client:
        config.qdrant_client = get_qdrant_client()

    user_id = "test-user"

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        config.session_id = st.session_state.session_id
        config.user_id = user_id
    init_session(st.session_state.session_id, user_id)

    if not config.DEBUG:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if config.DEBUG or uploaded_file is not None:
        try:
            if not config.DEBUG:
                os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
                with open(config.UPLOAD_PDF, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            if "rag_pipeline_initialized" not in st.session_state:
                with st.spinner("Processing PDF for Q&A... This may take a while."):
                    logger.info('Processing PDF for Q&A...')
                    setup_rag_pipeline(config.qdrant_client, config.UPLOAD_PDF, st.session_state.session_id)
                    st.session_state.rag_pipeline_initialized = True
                    st.success("PDF processed and ready for Q&A!")
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            st.error(f"Error processing PDF for Q&A: {e}")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if "is_translate" in message and message["is_translate"]:
                    display_pdf_translation(config.UPLOAD_PDF, config.PROCESSED_PDF)

                st.markdown(message["content"])
        
        
        render_quiz()

        if prompt := st.chat_input("Ask your question here"):
            logger.info(f"User asked: {prompt}")
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    
                    content = types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )

                    agent_runner = create_agent_runner()

                    events = agent_runner.run(user_id=user_id, session_id=st.session_state.session_id, new_message=content)
                    response = ""

                    for ev in events:
                        if ev.is_final_response():
                            response: str = ev.content.parts[0].text

                    logger.info(f"Model raw response: {response}")

                    # try to parse the json
                    try:
                        response = json.loads(response)
                    except:
                        response = {"model_response": response}

                    if "quiz_result" in response:
                        logger.info('Entering quiz mode ...')

                        try:
                            quiz_output = QuizOutput.model_validate(
                                response
                            )
                            logger.debug("Quiz output parsed successfully.")
                            
                            st.session_state.quiz_output = quiz_output
                            st.session_state.question_index = 0
                            st.session_state.score = 0
                            st.session_state.user_answers = {}

                            st.rerun()

                        except Exception as e:
                            logger.error(f"Failed to parse quiz data: {e}")
                            st.error(f"Failed to parse quiz data: {e}")
                            st.markdown(response.get('model_response', ''))


                    elif "translate_pdf" in response:
                        logger.info('Entering PDF translation mode ...')
                        
                        display_pdf_translation(config.UPLOAD_PDF, config.PROCESSED_PDF)
                        st.markdown(response["model_response"])
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response["model_response"],
                                "is_translate": True,
                            }
                        )
                    else:
                        logger.info(f"Displaying regular model response: {response.get('model_response', '')}")
                        st.markdown(response["model_response"])
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response["model_response"]}
                        )


if __name__ == "__main__":
    main()
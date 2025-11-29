import json
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)




def main():
    load_dotenv()

    st.set_page_config(page_title="PDF Agent", layout="wide")

    st.title("PDF Agent")

    qdrant_client = get_qdrant_client()

    user_id = "test-user"

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        config.session_id = st.session_state.session_id
        config.user_id = user_id

    init_session(st.session_state.session_id, user_id)

    if not config.DEBUG:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if config.DEBUG or uploaded_file is not None:
        if not config.DEBUG:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
            with open(UPLOAD_PDF, "wb") as f:
                f.write(uploaded_file.getbuffer())

        
        if "rag_pipeline_initialized" not in st.session_state:
            with st.spinner("Processing PDF for Q&A... This may take a while."):
                logging.info('qdrant database data:')
                records = get_all_collection_data(qdrant_client, st.session_state.session_id, False)
            
                if not records: # just in debug mode
                    setup_rag_pipeline(qdrant_client, config.UPLOAD_PDF, st.session_state.session_id)

                st.session_state.rag_pipeline_initialized = True
                st.success("PDF processed and ready for Q&A!")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        
        render_quiz()

        if prompt := st.chat_input("Ask your question here"):
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
                    logging.info(f"events: {events}")
                    for ev in events:
                        # logging.info(f"model: {ev.content.parts[0].text}")
                        if ev.is_final_response():
                            response: str = ev.content.parts[0].text

                    logging.info(f"model response: {response}")

                    # try to parse the json
                    try:
                        response = json.loads(response)
                    except:
                        response = {"model_response": response}

                    if "quiz_result" in response:
                        logging.info('enter quiz mode ...')

                        try:
                            quiz_output = QuizOutput.model_validate(
                                response
                            )
                            
                            st.session_state.quiz_output = quiz_output
                            st.session_state.question_index = 0
                            st.session_state.score = 0
                            st.session_state.user_answers = {}

                            st.rerun()

                        except Exception as e:
                            st.error(f"Failed to parse quiz data: {e}")
                            st.markdown(response.get('model_response', ''))


                    elif "translated_pdf" in response:
                        logging.info('enter pdf translation mode ...')
                        
                        display_pdf_translation(config.UPLOAD_PDF, config.PROCESSED_PDF)
                        st.markdown(response["model_response"])


                    else:
                        st.markdown(response["model_response"])
            st.session_state.messages.append(
                {"role": "assistant", "content": response["model_response"]}
            )


if __name__ == "__main__":
    main()
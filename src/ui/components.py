import time
import streamlit as st
import base64
import fitz # PyMuPDF
from io import BytesIO
from typing import Dict, Any

def display_pdf(pdf_path: str):
    """
    Displays a PDF file in the Streamlit app.
    """
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def display_pdf_translation(original_pdf_path: str, translated_pdf_path: str):
    """
    Displays original and translated PDF files side-by-side.
    """
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original PDF")
        display_pdf(original_pdf_path)
    with col2:
        st.subheader("Translated PDF")
        display_pdf(translated_pdf_path)

def display_pdf_qa(input_pdf_path: str):
    """
    Displays the original PDF for Q&A reference.
    """
    st.subheader("Original PDF for Reference")
    display_pdf(input_pdf_path)

def render_quiz():
    """
    Renders the interactive quiz.
    """

    if "quiz_output" not in st.session_state:
        return

    st.markdown("Here is your quiz:")

    if st.button("Close Quiz"):
        del st.session_state.quiz_output
        del st.session_state.question_index
        del st.session_state.score
        del st.session_state.user_answers
        st.rerun()

    question_index = st.session_state.question_index
    questions = st.session_state.quiz_output.questions

    if question_index < len(questions):
        question = questions[question_index]
        st.markdown(f"**Question {question_index + 1}:** {question.question}")

        if question.type == "multiple_choices" and question.choices:
            user_choice = st.radio("Choose your answer:", options=question.choices, key=f"question_{question_index}")

            if st.button("Submit Answer", key=f"submit_{question_index}"):
                st.session_state.user_answers[question_index] = user_choice
                if user_choice == question.correct_answer:
                    st.success("Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"Incorrect. The correct answer is: {question.correct_answer}")
                
                st.session_state.question_index += 1
                time.sleep(5)
                st.rerun()

        else: # open_ended
            if st.button("Show Answer", key=f"show_{question_index}"):
                st.markdown(f"**Answer:** {question.correct_answer}")
            if st.button("Next Question", key=f"next_{question_index}"):
                st.session_state.question_index += 1
                st.rerun()
    else:
        del st.session_state.quiz_output
        st.success(f"Quiz finished! Your score: {st.session_state.score}/{len(questions)}")
        time.sleep(10)
        st.rerun()
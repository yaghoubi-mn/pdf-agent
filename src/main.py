import streamlit as st

from src.ui.components import display_pdf_translation, display_pdf_qa, display_pdf_quiz

def main():
    st.set_page_config(page_title="PDF Agent", layout="wide")

    st.title("PDF Agent")

    st.sidebar.title("Features")
    feature = st.sidebar.radio("Choose a feature", ["PDF Translation", "PDF Q&A", "PDF Quiz Generation"])

    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        if feature == "PDF Translation":
            display_pdf_translation(uploaded_file)
        elif feature == "PDF Q&A":
            display_pdf_qa(uploaded_file)
        elif feature == "PDF Quiz Generation":
            display_pdf_quiz(uploaded_file)

if __name__ == "__main__":
    main()
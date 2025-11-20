# PDF Agent

This project is a PDF agent with the following features:

1.  **PDF Translation**: Extract text using PyMuPDF, create a copy of the PDF, and replace the original text with the translated text. The UI displays the original PDF on the left and the translated PDF on the right.
2.  **PDF Q&A**: Use Retrieval-Augmented Generation (RAG) and Qdrant for the vector database.
3.  **PDF Quiz Generation**.
4.  **User Interface**: Streamlit.

## Architecture

The project uses a modular architecture with a Streamlit front end and a Python back end. The back end is composed of a PDF agent core that orchestrates the different features.

## Getting Started

1.  Create a virtual environment:
2.  Install the dependencies:
3.  Run the Streamlit app
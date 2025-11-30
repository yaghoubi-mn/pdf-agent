# 🤖 PDF Agent

This project is a PDF agent that can help you with your PDF files. It can answer your questions based on the PDF, translate the entire PDF to another language, and generate quizzes based on the PDF.

## 🤔 The Problem

Working with large PDF documents can be a challenging and time-consuming task. Extracting specific information, translating content, or creating educational materials from these documents often requires manual effort, which is inefficient and prone to errors. Key challenges include:

-   **Information Retrieval**: Finding specific answers to questions within a lengthy PDF can be like searching for a needle in a haystack.
-   **Language Barriers**: Translating a PDF document into another language typically involves complex and often inaccurate tools, disrupting the original formatting.
-   **Content Engagement**: Manually creating quizzes or study materials from a PDF is a tedious process that can limit effective learning and engagement.

## 💡 The Solution

PDF Agent is an intelligent tool designed to streamline your interaction with PDF documents. By leveraging the power of Retrieval-Augmented Generation (RAG), this agent provides a seamless and efficient way to work with your files.

-   **RAG-Based Q&A**: Get precise answers to your questions from the PDF content.
-   **Full PDF Translation**: Translate the entire document while viewing the original and translated versions side-by-side.
-   **Automated Quiz Generation**: Instantly create quizzes based on the PDF’s content to enhance learning and retention.

## ✨ Project Features

-   **❓ Answer Questions**: Ask any question about the PDF, and the agent will find the answer for you.
-   **🌐 Translate PDF**: Translate the entire PDF to another language and see the original and translated versions side-by-side.
-   **📝 Generate Quiz**: Generate a quiz based on the PDF to test your knowledge.

## 🚀 How to Run the Project with Docker

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/pdf-agent.git
    cd pdf-agent
    ```
2.  **Create a `.env` file**:
    Create a `.env` file in the root of the project and add your `GEMINI_API_KEY`:
    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```
    You can also add this optional variables (recommanded).
    ```
    AGENT_MODEL_NAME="gemini-2.5-flash"
    TRANSLATOR_MODEL_NAME="gemini-2.5-flash-lite"
    ```
3.  **Build the Docker image**:
    ```bash
    docker build -t pdf-agent .
    ```
4.  **Run the Docker container**:
    ```bash
    docker run -p 8501:8501 --env-file .env pdf-agent
    ```
5.  **Open the application**:
    Open your browser and go to `http://localhost:8501`.

## ⏭️ Next Features Checklist

-   [ ] Add support for more languages in the translation feature.
-   [ ] Improve the quiz generation feature to support more question types.

## 📚 Documentation

### Project Structure

```
.
├── Dockerfile
├── LICENSE
├── README.md
├── requirements.txt
├── src
│   ├── agent
│   │   ├── core.py
│   │   ├── rag.py
│   │   └── ...
│   ├── pdf_tools
│   │   └── pdf_extractor.py
│   ├── pdf_translation
│   │   ├── pdf_translator.py
│   │   └── ...
│   ├── ui
│   │   └── components.py
│   └── main.py
└── tests
```

### How it Works

The project is built around a central agent that uses a set of tools to interact with PDF documents. The agent is defined in `src/agent/core.py` and uses the `google-adk` library to manage its functionalities.

#### The Agent

The agent is a `Gemini`-powered model responsible for understanding user requests and deciding which tool to use. It is configured with a specific set of instructions that guide its behavior, including how to format outputs for quizzes and translations.

#### Tools

The agent has access to the following tools:

-   **`search_pdf`**: This is the core of the RAG functionality. When a user asks a question, this tool searches the PDF for relevant information and provides it to the agent to generate an answer.
-   **`translate_pdf_tool`**: When a user requests a translation, this tool translates the entire PDF document.

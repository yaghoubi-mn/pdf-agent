import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from qdrant_client import QdrantClient
import fitz
import requests
import streamlit as st

from src.pdf_tools.pdf_extractor import extract_text_from_pdf, chunk_text
from src import config as project_config

from .vector_db import (
    get_qdrant_client,
    create_collection,
    upsert_vectors,
    search_vectors,
)

embedding_model = "models/embedding-gecko-001"

def save_vectors(
    qdrant_client: QdrantClient,
    collection_name: str,
    chunks: List[str],
    payloads: List[Dict[str, Any]],
    vector_size: int = 768,
) -> QdrantClient:
    """
    Generates embeddings for text chunks and saves them to a Qdrant collection.

    Args:
        collection_name: The name of the collection to save vectors to.
        chunks: A list of text chunks to be vectorized.
        payloads: A list of metadata for each chunk.
        vector_size: The dimensionality of the vectors.

    Returns:
        The Qdrant client instance used for the operation.
    """

    create_collection(qdrant_client, collection_name, vector_size)
    
    embeddings = generate_embeddings(chunks)
    
    if embeddings:
        upsert_vectors(client, collection_name, embeddings, payloads)
    
    return client

def search_pdf(query: str) -> List[Dict[str, Any]]:
    """
    Searches the Qdrant collection for a given query.

    Args:
        query: The search query string.

    Returns:
        A list of search result payloads.
    """

    logging.info(f"The model searched pdf with this query: {query}")
    
    if project_config.DEBUG:
        with open('data/query_embedding.json', 'r') as f:
            query_embedding = json.loads(f.read())['embedding']
    else:
        query_embedding = generate_embeddings([query])
    
    if not query_embedding:
        logging.warning("query embbeing is empty")
        return []

    search_results = search_vectors(
        project_config.qdrant_client,
        project_config.session_id,
        query_embedding[0],
        5,
    )

    logging.info(f'found {len(search_results)} embedding result')
    
    return [result.payload for result in search_results]




def generate_embeddings(chunks: List[str], model: str = "models/gemini-embedding-001") -> List[List[float]]:
    """
    Generates embeddings for a list of text chunks.

    Args:
        chunks: A list of text chunks to embed.
        model: The name of the embedding model to use.

    Returns:
        A list of embeddings, where each embedding is a list of floats.
    """
    if not chunks:
        return []

    for _ in range(10):
        try:
            # for self hosted embedding model
            if project_config.EMBEDDING_URL:
                payload = {
                    "input": text,
                    "model": "gemmaembedding-300m"
                }
                response = requests.post(project_config.EMBEDDING_URL,json=payload)
                response.raise_for_status()
                return response.json()['data'][0]['embedding']
            else:
                result = genai.embed_content(
                    model=model,
                    content=chunks,
                    task_type="retrieval_document"
                )
                return result['embedding']
        except Exception as e:
            logging.error(f"Error generating embeddings: {e}")
        
    return []


def setup_rag_pipeline(qdrant_client, pdf_path: str, collection_name: str):
    """
    Sets up the RAG pipeline by processing the PDF, generating embeddings,
    and storing them in a Qdrant collection.

    Args:
        pdf_path: The path to the PDF file.
        collection_name: The name of the collection to create in Qdrant.

    Returns:
        The Qdrant client.
    """

    if project_config.DEBUG:
        with open('data/embedding.json', 'r') as f:
            embeddings = json.loads(f.read())
        with open('data/chunks.json', 'r') as f:
            chunks = json.loads(f.read())
    else:        
        # Extract text from the PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return None

        # Chunk the text
        chunks = chunk_text(text)

        # Generate embeddings for the chunks
        logging.info('generating embedding ...')
        embeddings = generate_embeddings(chunks)
        if not embeddings:
            return None
        # else:
            # with open('data/embedding.json', 'w') as f:
            #     f.write(json.dumps(embeddings))

    # Set up the vector database
    if embeddings:
        vector_size = len(embeddings[0])
        create_collection(qdrant_client, collection_name, vector_size, project_config.RECREATE_COLLECTION)
        payloads = [{"text": chunk} for chunk in chunks]
        upsert_vectors(qdrant_client, collection_name, embeddings, payloads)
    else:
        print("No embeddings generated, skipping collection creation and upsert.")

    return qdrant_client


def get_pdf_page(page_num: int):
    pdf = fitz.open(project_config.UPLOAD_PDF)
    page = pdf.load_page(page_num)
    return str(page.get_text())
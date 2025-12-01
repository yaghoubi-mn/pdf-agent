import json
from typing import List, Dict, Any
import google.generativeai as genai
from qdrant_client import QdrantClient
import fitz
import requests
import streamlit as st

from src.pdf_tools.pdf_extractor import extract_text_from_pdf, chunk_text
from src import config as project_config
from src.config import logger

from .vector_db import (
    create_collection,
    upsert_vectors,
    search_vectors,
)


def save_vectors(
    qdrant_client: QdrantClient,
    collection_name: str,
    chunks: List[str],
    payloads: List[Dict[str, Any]],
    vector_size: int = 768,
):
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
    logger.debug(f"Saving vectors to collection: {collection_name}")
    try:
        create_collection(qdrant_client, collection_name, vector_size)
        
        embeddings = generate_embeddings(chunks)
        
        if embeddings:
            upsert_vectors(qdrant_client, collection_name, embeddings, payloads)
            logger.info(f"Successfully upserted {len(embeddings)} vectors to collection {collection_name}.")
        else:
            logger.warning("No embeddings generated, skipping vector upsert.")
    except Exception as e:
        logger.error(f"Error saving vectors to collection {collection_name}: {e}")
        raise
    


def search_pdf(query: str) -> List[Dict[str, Any]]:
    """
    Searches the Qdrant collection for a given query.

    Args:
        query: The search query string.

    Returns:
        A list of search result payloads.
    """
    logger.info(f"Searching PDF with query: '{query}'")
    
    try:
        if project_config.DEBUG:
            with open('data/query_embedding.json', 'r') as f:
                query_embedding = json.loads(f.read())['embedding']
        else:
            query_embedding = generate_embeddings([query])
        
        if not query_embedding:
            logger.warning("Query embedding is empty, cannot perform search.")
            return []

        search_results = search_vectors(
            project_config.qdrant_client,
            project_config.session_id,
            query_embedding[0],
            5,
        )

        logger.info(f"Found {len(search_results)} embedding results for query: '{query}'")
        
        return [result.payload for result in search_results]
    except Exception as e:
        logger.error(f"Error during PDF search for query '{query}': {e}")
        return []




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
            logger.info(f'Using selfhosted embedding model with {project_config.EMBEDDING_URL}')
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
            logger.error(f"Error generating embeddings: {e}")
        
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
    logger.info(f"Setting up RAG pipeline for PDF: {pdf_path}, collection: {collection_name}")

    try:
        if project_config.DEBUG:
            logger.debug("Debug mode: Loading embeddings and chunks from local files.")
            with open('data/embedding.json', 'r') as f:
                embeddings = json.loads(f.read())
            with open('data/chunks.json', 'r') as f:
                chunks = json.loads(f.read())
        else:
            # Extract text from the PDF
            text = extract_text_from_pdf(pdf_path)
            if not text:
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                return None

            # Chunk the text
            chunks = chunk_text(text)
            logger.info(f"Extracted {len(chunks)} chunks from PDF.")

            # Generate embeddings for the chunks
            logger.info('Generating embeddings for chunks...')
            embeddings = generate_embeddings(chunks)
            if not embeddings:
                logger.error("Failed to generate embeddings for chunks.")
                return None

        # Set up the vector database
        if embeddings:
            vector_size = len(embeddings[0])
            logger.info(f"Creating/recreating Qdrant collection '{collection_name}' with vector size {vector_size}. Recreate: {project_config.RECREATE_COLLECTION}")
            create_collection(qdrant_client, collection_name, vector_size, project_config.RECREATE_COLLECTION)
            payloads = [{"text": chunk, "page_num": i+1} for i, chunk in enumerate(chunks)] # Added page_num to payload
            logger.info(f"Upserting {len(embeddings)} vectors into collection '{collection_name}'.")
            upsert_vectors(qdrant_client, collection_name, embeddings, payloads)
            logger.info(f"RAG pipeline setup complete for collection: {collection_name}")
        else:
            logger.warning("No embeddings generated, skipping collection creation and upsert.")

        return qdrant_client
    except Exception as e:
        logger.error(f"Error setting up RAG pipeline for {pdf_path}: {e}")
        return None


@st.cache_data
def get_pdf_page(page_num: int):
    logger.debug(f"Getting page {page_num} from PDF: {project_config.UPLOAD_PDF}")
    try:
        pdf = fitz.open(project_config.UPLOAD_PDF)
        page = pdf.load_page(page_num)
        return str(page.get_text())
    except Exception as e:
        logger.error(f"Error getting page {page_num} from PDF: {e}")
        return ""
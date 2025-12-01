from qdrant_client import QdrantClient, models
from src import config as project_config
from src.config import logger




def get_qdrant_client():
    """Initializes and returns a Qdrant client."""
    logger.info("Initializing Qdrant client.")
    if project_config.DEBUG:
        logger.debug("Qdrant client: connecting to localhost:6333 (debug mode).")
        return QdrantClient(host="localhost", port=6333)
    else:
        logger.debug("Qdrant client: connecting to in-memory instance.")
        return QdrantClient(":memory:")



def get_all_collection_data(client: QdrantClient, collection_name: str, raise_error: bool = True):
    logger.info(f"Retrieving all collection data for '{collection_name}'.")
    try:
        records, _ = client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=True,
        )
        logger.info(f"Retrieved {len(records)} records from collection '{collection_name}'.")
        return records
    except Exception as e:
        logger.error(f"Error retrieving collection data for '{collection_name}': {e}")
        if raise_error:
            raise e
        return []
    


def create_collection(client: QdrantClient, collection_name: str, vector_size: int, recreate: bool = True):
    """
    Creates a new collection in Qdrant if it doesn't already exist.

    Args:
        client: The Qdrant client.
        collection_name: The name of the collection.
        vector_size: The size of the vectors to be stored.
    """
    logger.info(f"Attempting to create collection '{collection_name}' (recreate: {recreate}).")
    try:
        if recreate:
            result = client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            logger.info(f"Collection '{collection_name}' recreated with result: {result}.")
        else:
            result = client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            logger.info(f"Collection '{collection_name}' created with result: {result}.")

        if not result:
            logger.error(f"Failed to create collection '{collection_name}'.")
    except Exception as e:
        logger.error(f"Error in creating collection '{collection_name}': {e}")
        raise

def upsert_vectors(client: QdrantClient, collection_name: str, vectors, payloads):
    """
    Inserts or updates vectors in a specified collection.

    Args:
        client: The Qdrant client.
        collection_name: The name of the collection.
        vectors: The vectors to be upserted.
        payloads: The corresponding payloads for the vectors.
    """
    logger.info(f"Upserting {len(vectors)} vectors into collection '{collection_name}'.")
    try:
        client.upsert(
            collection_name=collection_name,
            points=models.Batch(
                ids=[i for i in range(len(vectors))],
                vectors=vectors,
                payloads=payloads
            ),
            wait=True,
        )
        logger.info(f"Successfully upserted {len(vectors)} vectors into collection '{collection_name}'.")
    except Exception as e:
        logger.error(f"Error upserting vectors into collection '{collection_name}': {e}")
        raise

def search_vectors(client: QdrantClient, collection_name: str, query_vector, limit: int = 5):
    """
    Searches for similar vectors in a collection.

    Args:
        client: The Qdrant client.
        collection_name: The name of the collection.
        query_vector: The vector to search with.
        limit: The maximum number of results to return.

    Returns:
        A list of search results.
    """
    logger.info(f"Searching for {limit} vectors in collection '{collection_name}'.")
    try:
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
        ).points
        logger.info(f"Found {len(results)} vectors in collection '{collection_name}'.")
        return results
    except Exception as e:
        logger.error(f"Error searching vectors in collection '{collection_name}': {e}")
        raise
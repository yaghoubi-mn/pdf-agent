from qdrant_client import QdrantClient, models

def get_qdrant_client():
    """Initializes and returns a Qdrant client."""
    return QdrantClient(host="localhost", port=6333)
    # return QdrantClient(":memory:")


def get_all_collection_data(client: QdrantClient, collection_name: str, raise_error: bool = True):

    try:
        records, next_offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=True,
        )

        return records
    except Exception as e:
        if raise_error:
            raise e
    


def create_collection(client: QdrantClient, collection_name: str, vector_size: int, recreate: bool = True):
    """
    Creates a new collection in Qdrant if it doesn't already exist.

    Args:
        client: The Qdrant client.
        collection_name: The name of the collection.
        vector_size: The size of the vectors to be stored.
    """
    try:
        if recreate:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
        else:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
    except Exception as e:
        print(f"Error creating collection: {e}")

def upsert_vectors(client: QdrantClient, collection_name: str, vectors, payloads):
    """
    Inserts or updates vectors in a specified collection.

    Args:
        client: The Qdrant client.
        collection_name: The name of the collection.
        vectors: The vectors to be upserted.
        payloads: The corresponding payloads for the vectors.
    """
    client.upsert(
        collection_name=collection_name,
        points=models.Batch(
            ids=[i for i in range(len(vectors))],
            vectors=vectors,
            payloads=payloads
        ),
        wait=True,
    )

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
    return client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
    ).points
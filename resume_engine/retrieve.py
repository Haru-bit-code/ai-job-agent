# ──────────────────────────────────────────────────────────────
# PURPOSE: Given a job description, retrieve the most relevant
#          sections from the stored resume in ChromaDB
# ──────────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
import chromadb

from resume_engine.embed import MODEL_NAME, CHROMA_PATH, COLLECTION_NAME


_model = None  # global model cache

def get_embedding_model():
    """Load model once, reuse for all subsequent calls."""
    global _model
    if _model is None:
        print("  → Loading embedding model (first time only)...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_relevant_chunks(job_description: str, top_k: int = 3) -> list[dict]:
    
    model = get_embedding_model()  # ← replaces SentenceTransformer(MODEL_NAME)
    
    # rest of function stays exactly the same


def get_relevant_chunks(job_description: str, top_k: int = 3) -> list[dict]:
    """
    Takes a job description string.
    Returns the top_k most relevant resume chunks.

    top_k = how many chunks to return
            3 is usually ideal — enough context, not too noisy
    """

    # Load the same model used during embedding
    # CRITICAL: must be the same model, or vectors are incompatible
    # Different models = different vector spaces = wrong results
    model = SentenceTransformer(MODEL_NAME)

    # Connect to the existing ChromaDB (already has your resume)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    # Convert the job description into an embedding
    # Same process as before — text becomes 384 numbers
    job_embedding = model.encode(job_description).tolist()

    # Query ChromaDB
    # "Find me the top_k chunks whose embeddings are
    #  closest to this job_embedding"
    results = collection.query(
        query_embeddings=[job_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
        # distances = how similar each result is
        # lower distance = more similar (cosine distance)
    )

    # ChromaDB returns results in a nested structure
    # results["documents"][0] = list of matched texts
    # results["metadatas"][0] = list of metadata dicts
    # results["distances"][0] = list of similarity scores
    # The [0] is because we sent one query — it wraps in a list

    chunks = []

    for i in range(len(results["documents"][0])):
        chunk = {
            "section":   results["metadatas"][0][i]["section"],
            "content":   results["documents"][0][i],
            "distance":  round(results["distances"][0][i], 4)
            # distance: 0.0 = identical, 1.0 = completely different
            # good results are usually between 0.2 - 0.6
        }
        chunks.append(chunk)

    return chunks


def format_chunks_for_llm(chunks: list[dict]) -> str:
    """
    Takes the retrieved chunks and formats them into
    a single clean string ready to be injected into an LLM prompt.

    This is what the GenAI writer will receive as context.
    """
    formatted = []

    for i, chunk in enumerate(chunks, 1):
        formatted.append(
            f"[Resume Section {i}: {chunk['section']}]\n{chunk['content']}"
        )

    return "\n\n".join(formatted)


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":

    # Simulate a real job description
    test_job = """
    We are looking for a Data Scientist with experience in 
    machine learning, Python, and NLP. The candidate should 
    have built predictive models and worked with real datasets.
    Experience with scikit-learn, pandas, and data visualization 
    is required. Knowledge of LLMs or RAG systems is a plus.
    """

    print("=== JOB DESCRIPTION ===")
    print(test_job.strip())

    print("\n=== RETRIEVING RELEVANT RESUME SECTIONS ===\n")

    chunks = get_relevant_chunks(test_job, top_k=3)

    for chunk in chunks:
        print(f"── {chunk['section']} (distance: {chunk['distance']}) ──")
        print(chunk['content'][:200])
        print()

    print("\n=== FORMATTED FOR LLM ===\n")
    print(format_chunks_for_llm(chunks))
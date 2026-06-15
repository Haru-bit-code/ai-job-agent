# ──────────────────────────────────────────────────────────────
# PURPOSE: Convert resume text chunks into embeddings (vectors)
# and store them in ChromaDB for semantic search later
# ──────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
import chromadb
import os

# ── CONFIG ───────────────────────────────────────────────────
# This model runs on CPU, is small (80MB), and works very well
# for semantic similarity tasks like resume-job matching
MODEL_NAME = "all-MiniLM-L6-v2"

# Where ChromaDB will save its data on your disk
# This folder will be created automatically
CHROMA_PATH = "data/chroma_db"

# The name of our collection inside ChromaDB
# Think of a collection like a table in a regular database
COLLECTION_NAME = "resume_chunks"


def get_embedding_model() -> SentenceTransformer:
    """
    Loads the embedding model.
    First time: downloads from internet (~80MB, one time only)
    After that: loads from local cache instantly
    """
    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded successfully.")
    return model


def get_chroma_collection():
    """
    Creates (or connects to) ChromaDB and returns our collection.
    
    ChromaDB is a vector database — it stores embeddings and
    lets us search them by similarity.
    
    Think of it like SQLite but for vectors instead of tables.
    """
    # PersistentClient saves data to disk so it survives restarts
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # get_or_create: if collection exists, use it
    #                if not, create it fresh
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
        # cosine = measure similarity by angle between vectors
        # best choice for text similarity tasks
    )
    
    return collection


def embed_and_store(chunks: list[dict]) -> None:
    """
    Takes resume chunks.
    Converts each to an embedding.
    Stores everything in ChromaDB.
    """
    
    model = get_embedding_model()
    collection = get_chroma_collection()
    
    # Check if we already have data stored
    # Avoids duplicating entries if you run this twice
    existing = collection.count()
    if existing > 0:
        print(f"Collection already has {existing} chunks.")
        print("Clearing old data and re-embedding...")
        # Delete all existing records
        collection.delete(where={"section": {"$ne": ""}})
    
    print(f"\nEmbedding {len(chunks)} chunks...")
    
    # Prepare data for ChromaDB
    # ChromaDB needs three parallel lists:
    #   ids       → unique identifier for each chunk
    #   documents → the actual text content
    #   metadatas → extra info we want to store alongside
    
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    for chunk in chunks:
        # Extract text to embed
        text = chunk["content"]
        
        # Generate embedding — this is the core operation
        # encode() runs the text through the neural network
        # returns a numpy array of 384 numbers
        embedding = model.encode(text)
        
        ids.append(chunk["chunk_id"])
        documents.append(text)
        metadatas.append({"section": chunk["section"]})
        
        # Convert numpy array to plain Python list
        # ChromaDB requires plain lists, not numpy arrays
        embeddings.append(embedding.tolist())
        
        print(f"  ✓ Embedded: {chunk['section']} ({len(text)} chars)")
    
    # Store everything in ChromaDB in one batch operation
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )
    
    print(f"\n✅ Successfully stored {len(chunks)} chunks in ChromaDB")
    print(f"   Database location: {CHROMA_PATH}")


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from extract import extract_text_from_pdf
    from chunk import chunk_resume
    
    # Step 1: Extract
    print("=== STEP 1: Extracting text ===")
    text = extract_text_from_pdf("data/resume.pdf")
    
    # Step 2: Chunk
    print("\n=== STEP 2: Chunking ===")
    chunks = chunk_resume(text)
    print(f"Found {len(chunks)} chunks")
    
    # Step 3: Embed and store
    print("\n=== STEP 3: Embedding and storing ===")
    embed_and_store(chunks)
    
    print("\n=== DONE ===")
    print("Your resume is now stored as searchable vectors in ChromaDB.")
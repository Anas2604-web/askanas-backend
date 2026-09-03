from dotenv import load_dotenv
load_dotenv()

from app.retrieval.ingest import load_all_project_chunks
from app.retrieval.qdrant_store import upsert_to_qdrant

if __name__ == "__main__":
    chunks = load_all_project_chunks()
    print(f"Loaded {len(chunks)} chunks from {len(set(c.project_title for c in chunks))} project docs.")
    upsert_to_qdrant(chunks)
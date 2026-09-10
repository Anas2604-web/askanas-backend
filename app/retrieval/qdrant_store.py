import os
import glob
from dataclasses import dataclass
import re
from dotenv import load_dotenv
load_dotenv()
from app.retrieval.ingest import ProjectChunk, embed_chunks
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

COLLECTION_NAME= "askanas_projects"
client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY", None),
    timeout=60,
)
model=TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def retrieve_projects(query: str, top_k: int =5):
    query_vector=list(model.embed([query]))[0]
    results= client.query_points(
              collection_name=COLLECTION_NAME,
              query=query_vector,
              limit=top_k).points
    return [
        {
        "content": r.payload["content"],
        "project_title": r.payload["project_title"],
        "section_title": r.payload["section_title"],
        "source_file": r.payload["source_file"],
    }
    for r in results
]


def upsert_to_qdrant(chunks: list[ProjectChunk], collection_name: str = "askanas_projects", batch_size: int = 20):
    """Embed all chunks and upsert them into Qdrant as points with metadata payloads, in batches."""

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    texts = [chunk.content for chunk in chunks]
    vectors = embed_chunks(texts)

    points = [
        PointStruct(
            id=i,
            vector=vectors[i],
            payload={
                "content": chunk.content,
                "project_title": chunk.project_title,
                "section_title": chunk.section_title,
                "source_file": chunk.source_file,
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        print(f"  Upserted batch {i // batch_size + 1} ({len(batch)} points)")

    print(f"Upserted {len(points)} chunks into '{collection_name}'.")

def list_all_projects() -> list[dict]:
    all_points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=200,
        with_payload=True,
    )

    seen = {}
    for point in all_points:
        title = point.payload["project_title"]
        if title in {"Contacts", "Internship", "Resume", "CareerPositioning"}:
            continue
        section = point.payload["section_title"]
        if title not in seen or section == "One-line summary":
            seen[title] = point.payload

    return list(seen.values())

if __name__ == "__main__":
    results = retrieve_projects("what is Anas's Teamwork Experience?")
    for r in results:
        print(r["project_title"], "→", r["section_title"])
        print(r["content"][:150], "...\n")
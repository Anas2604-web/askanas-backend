import os
import glob
from dataclasses import dataclass
import re
from ingest import ProjectChunk
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

COLLECTION_NAME= "askanas_projects"
client = QdrantClient(url="http://localhost:6333")
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


def upsert_to_qdrant(chunks: list[ProjectChunk], collection_name: str = "askanas_projects"):
    """Embed all chunks and upsert them into Qdrant as points with metadata payloads."""

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

    client.upsert(collection_name=collection_name, points=points)
    print(f"Upserted {len(points)} chunks into '{collection_name}'.")

if __name__ == "__main__":
    results = retrieve_projects("what is Anas's Teamwork Experience?")
    for r in results:
        print(r["project_title"], "→", r["section_title"])
        print(r["content"][:150], "...\n")
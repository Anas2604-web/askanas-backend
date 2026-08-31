# DevDocs AI

## One-line summary
A multi-tenant B2B RAG SaaS that lets companies upload their internal docs and get accurate, hallucination-filtered answers via a chat interface — currently built in Java/Spring Boot (not yet ported to the FastAPI/Python stack used elsewhere).

## Project Ranking
Rated 8/10 by Anas. A solid multi-tenant B2B RAG SaaS with real production concerns (4-layer tenant isolation, confidence-threshold filtering, Redis caching cutting LLM cost ~65%). Currently still on the Java/Spring Boot stack, with a Python/FastAPI port planned but not yet complete — worth noting if asked about current stack limitations.

## Problem / context
Companies need a way to make internal documentation searchable and queryable without engineering teams building custom RAG infra from scratch. DevDocs AI packages that as a multi-tenant SaaS — multiple customer orgs share the same deployment but stay fully data-isolated.

## Architecture
Spring Boot backend handles auth, multi-tenancy, and orchestration. Ingestion pipeline: documents → chunked → embedded → stored in Pinecone. Query pipeline: user question → retrieval → confidence-threshold hallucination filtering → Cohere reranking → SSE-streamed LLM answer. Redis used for both response caching and rate limiting. Next.js frontend. Deployed on AWS EC2.

## Tech stack
Java, Spring Boot, Next.js, Pinecone, Redis, Groq, AWS EC2, Flyway (schema migrations), JWT.

## Key decisions & why
- **4-layer multi-tenant isolation** (JWT claims, ThreadLocal context, SQL row-level filtering, Pinecone namespace separation) — layered defense so a single point of failure can't leak one tenant's data into another's results, which matters a lot for a B2B SaaS handling customer documents.
- **Confidence-threshold hallucination filtering before Cohere reranking** — reject low-confidence retrieved chunks before they ever reach the reranker/generation step, rather than relying on the LLM alone to avoid hallucinating from weak context.
- **Redis caching** — cut LLM cost ~65% by caching repeated/similar queries instead of hitting the LLM API every time.
- **Flyway for schema migrations** — versioned, repeatable DB schema changes, standard production practice for a multi-tenant relational schema.

## Challenges & fixes
- **Auth not persisting on refresh** — dashboard would lose auth state on page refresh; fixed with a hydration guard in the dashboard layout to correctly rehydrate auth state client-side.
- **SSE auth for streamed chat** — SSE connections needed their own auth handling separate from normal REST auth; fixed alongside adding a dashboard stats endpoint.
- **Getting the ingestion pipeline working end-to-end** — first real milestone was 5 chunks successfully embedded into Pinecone, validating the full chunk → embed → store path before scaling up.
- **Building the full production RAG pipeline in stages** — auth/multi-tenancy/Redis first, then ingestion, then the RAG chat itself with SSE streaming and rate limiting, then confidence filtering + reranking + hallucination prevention as a distinct later pass — shows an incremental, production-style build order rather than trying to ship everything at once.

## Results / metrics
~65% LLM cost reduction via Redis caching. 4-layer tenant isolation. Deployed live at devdocsai.online on AWS EC2.

## Status note
Currently Java/Spring Boot — a Python/FastAPI port is planned but not yet done. [Anas: update this doc once you migrate and pull real updated metrics/architecture.]

## Links
GitHub: https://github.com/Anas2604-web/devdocs-ai
Live: devdocsai.online
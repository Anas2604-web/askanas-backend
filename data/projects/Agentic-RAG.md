# AgenticRAG

## One-line summary
A document Q&A platform where the AI doesn't just retrieve-and-answer — it acts as an agent that plans, retrieves, checks if what it found is actually good enough, and re-queries if not, citing exact source/chunk/passage every time. Built with teammate Arvinder Singh Dhoul as a major/final-year project.

## Project Ranking
Rated 8/10 by Anas. His primary final-year major project, built with teammate Arvinder Singh Dhoul under faculty guidance. Strong technical story around agentic retrieval loops and citation accuracy, and his main teamwork/collaboration STAR example — but not rated as high as RepoMind or UPI Offline Mesh in raw technical depth.

## Problem / context
Standard RAG retrieves once and generates from whatever it finds, with no way to tell if the retrieved context was actually relevant — leading to vague, unverifiable "based on your document" answers. AgenticRAG treats retrieval as a decision the LLM makes and can revisit, not a fixed first step.

## Architecture
Next.js frontend with a 3-panel research UI (sources · chat · citations). Users upload PDF/DOCX/TXT/MD, which is chunked and indexed into Qdrant. A LangGraph-orchestrated agent loop handles the retrieval decision-making: plan → retrieve → evaluate relevance → re-query if insufficient → generate with inline citations. Session data and auth stored in MongoDB via NextAuth.js.

## Tech stack
Next.js, TypeScript, LangGraph, LangChain, Qdrant, MongoDB, Groq, NextAuth.js.

## Key decisions & why
- **Agentic retrieval loop over plain RAG** — the core differentiator: standard RAG can't tell if retrieved chunks are relevant and has no course-correction; making the LLM an agent that evaluates its own retrieval quality and re-queries when needed produces far more reliable, citation-backed answers.
- **Full source attribution / pinpoint citations** — every answer traces to exact document, chunk, and passage, which was the single most validated feature during testing — directly addresses the "trust me" problem with typical RAG output.
- **3-panel UI (sources/chat/citations)** — designed so the reasoning and evidence are visible alongside the answer, not hidden behind it — an actual product decision, not just a technical one.

## Challenges & fixes
- **Iterative pipeline build order** — started with core RAG (embeddings, Qdrant storage, retrieval), then added source attribution/citations as a distinct pass, then layered in the full agentic pipeline with a fallback mechanism and context-based answering — incremental hardening rather than a single big-bang implementation.
- **Deployment platform churn** — hit multiple build/deploy issues getting a Next.js + LangChain + Qdrant stack running in production: needed `serverExternalPackages` config for LangChain/Qdrant, had to downgrade Next.js versions, add `legacy-peer-deps` for Railway, adjust Next config specifically for the Railway build, and add global error boundaries and a not-found page for production robustness.
- **Team split** — Arvinder owned document upload UI, auth, session naming, and general product polish, while Anas focused on the agentic RAG core (embedder, dimension validation, retriever wrapping Qdrant search with logging, the LangGraph orchestration itself) — a genuine division of labor, not just pair-programming the same thing.

## Results / metrics
Fully working agentic retrieval loop with accurate pinpoint citations (document/chunk/line level), validated directly by user testing during the build. Deployed to production (Railway).

## Collaboration note
Built with Arvinder Singh Dhoul as final-year major project, under guidance of Dr. Ritu Ahluwalia. This is your primary teamwork/collaboration STAR story — Arvinder handled UI/session/auth features while you owned the agentic core, a clean example of real task division you can speak to concretely.

## Links
GitHub: https://github.com/Anas2604-web/RAG
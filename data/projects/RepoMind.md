# RepoMind

## One-line summary
An agentic RAG platform that lets developers paste any GitHub repo URL and ask natural-language questions, answered with exact file + line citations.

## Problem / context
Contributing to unfamiliar open-source codebases is slow — a 200-file repo with no explanation means hours of manual reading before you can make a useful change. RepoMind clones the repo, indexes it, and lets you ask questions directly instead.

## Architecture
User submits a repo URL → backend clones it → chunks every file into semantic segments → builds a Qdrant vector index → a LangGraph ReAct agent decides when and how to search that index → answers stream back token-by-token via SSE with clickable file/line citations that jump to the exact location in a file tree UI.

## Tech stack
FastAPI, LangGraph (ReAct agent), Qdrant, fastembed, Groq (llama-3.1-8b-instant), Next.js 14, Clerk (auth), PostHog (analytics). Deployed: Vercel (frontend) + Render (backend) + Qdrant Cloud.

## Key decisions & why
- **fastembed (ONNX) over sentence-transformers/PyTorch** — Render's free tier caps RAM at 512MB; PyTorch alone was ~1.2GB, causing OOM crashes. Switching to ONNX-based fastembed cut memory ~96% (1.2GB → ~50MB), fixing the crash at the root instead of just tuning batch sizes.
- **Batched embeddings** — reduced memory spikes during indexing, an incremental fix before landing on the fastembed switch.
- **CPU-only torch build** — used for the Render deploy specifically, before fully removing PyTorch dependency.
- **LangGraph ReAct agent over plain RAG** — the agent decides *when* to search rather than retrieving unconditionally on every query, which is more efficient and lets it reason about ambiguous questions before searching.

## Challenges & fixes
- **OOM crash on Render free tier** — root-caused to PyTorch's memory footprint; fixed by switching the entire embedding pipeline to fastembed/ONNX (commit: "Switch to fastembed (ONNX) - drops PyTorch entirely, fixes Render OOM at the root").
- **JWT expiry on cold starts** — Render free-tier cold starts caused tokens to expire mid-request, producing confusing 401 errors; fixed by adding leeway handling and proper 401/429 error messaging so users get clear feedback instead of silent failures.
- **Citation extraction bug during streaming** — citations weren't reliably extracted when responses were streamed; fixed by pulling citations from tool messages specifically rather than parsing the streamed text.
- **Persistent "thinking bubble" UI bug** — the thinking indicator stayed visible during token streaming; fixed by hiding it properly mid-stream and cleaning up a stray newline before the citations marker.
- **CORS issues in production** — forced wildcard origins to handle cross-origin requests robustly between the Vercel frontend and Render backend.
- **Groq tool-calling reliability** — Groq's tool-calling has a documented bug where it can break mid-stream; built auto-retry handling around it.
- **Deployment config churn** — multiple iterations getting `vercel.json` right for a frontend-only deploy (framework field, entrypoint, experimental services format) before settling on a clean split: frontend on Vercel, backend on Render.

## Results / metrics
~96% RAM reduction (1.2GB → ~50MB) via the fastembed switch, which was the difference between the backend crashing and running stably on a free-tier 512MB instance. SSE token-by-token streaming so responses feel immediate rather than a 10-second frozen wait.

## Collaboration note
UI/onboarding tour and file-tree interactions built in collaboration with Aryan Barde — worth mentioning in interviews as a real teamwork example distinct from your AgenticRAG teamwork story with Arvinder.

## Links
GitHub: https://github.com/Anas2604-web/repomind
Live demo: repomind-nu.vercel.app
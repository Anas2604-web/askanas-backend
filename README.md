# AskAnas

**A live AI agent that replaces a static resume — talk to it instead of reading a PDF.**

🔗 **Live:** [askanas.vercel.app](https://askanas.vercel.app)
🎥 Ask it: *"What's Anas's best project?"* or *"Why did he choose fastembed over sentence-transformers?"*

---

## What this is

AskAnas is a production agentic RAG system: a LangGraph ReAct agent that retrieves grounded facts from a Qdrant vector store of the author's real project documentation, answers with citations, streams responses token-by-token, and refuses to hallucinate or drift off-topic — enforced by LLM-as-judge guardrails, not just a system prompt and hope.

It is not a wrapped ChatGPT call. Every claim above is independently verifiable via the [LangSmith trace](#observability) attached to any live request.

---

## Architecture

```
┌──────────────┐      POST /chat/stream       ┌───────────────────────┐
│   Next.js 14  │ ───────────────────────────▶ │       FastAPI          │
│   (Vercel)    │ ◀─────────────────────────── │       (Render)         │
│  SSE client   │      token-by-token SSE      │                        │
└──────────────┘                               └───────────┬────────────┘
                                                            │
                                          ┌─────────────────▼──────────────────┐
                                          │      Input Guardrail (LLM Judge)    │
                                          │  blocks: injection, off-topic,      │
                                          │  PII/contact-leak requests          │
                                          └─────────────────┬────────────────────┘
                                                            │ safe
                                          ┌─────────────────▼──────────────────┐
                                          │        LangGraph ReAct Agent        │
                                          │                                     │
                                          │   ┌─────────────┐  ┌─────────────┐  │
                                          │   │project_     │  │list_        │  │
                                          │   │retrieval    │  │projects     │  │
                                          │   │  (tool)     │  │  (tool)     │  │
                                          │   └──────┬──────┘  └──────┬──────┘  │
                                          └──────────┼────────────────┼─────────┘
                                                     │                │
                                          ┌──────────▼────────────────▼─────────┐
                                          │        Qdrant Cloud (vector DB)      │
                                          │   96 chunks · 10 project docs        │
                                          │   fastembed (ONNX, 384-dim)          │
                                          └───────────────────────────────────────┘
                                                            │
                                          ┌─────────────────▼──────────────────┐
                                          │     Output Guardrail (LLM Judge)    │
                                          │   flags: ungrounded claims,          │
                                          │   off-topic drift, info leaks        │
                                          └─────────────────┬────────────────────┘
                                                            │
                                          ┌─────────────────▼──────────────────┐
                                          │   LangSmith (full request tracing)  │
                                          │   PostHog (engagement analytics)     │
                                          └───────────────────────────────────────┘
```

**Flow:** user asks a question → input guardrail (LLM-as-judge) screens for injection/off-topic/PII-extraction attempts → LangGraph agent decides whether to call `project_retrieval` (semantic search) or `list_projects` (deterministic full listing) → Qdrant returns grounded context → agent generates a cited answer, streamed via SSE → output guardrail flags any drift → every step logged to LangSmith.

---

## Why agentic, not plain RAG

Plain RAG retrieves once and generates — no way to know if retrieval actually helped. This system's ReAct agent *decides* when to search versus answer directly, and routes list-style questions ("what projects has he built?") to a deterministic tool instead of a similarity search, since exhaustive enumeration is a coverage problem, not a relevance-ranking problem. Two different query types, two different retrieval strategies, chosen deliberately rather than forcing one tool to do both jobs.

---

## Guardrails

Both layers are LLM-as-judge, not regex — because prompt injection phrasing is infinite and regex only catches phrasing you thought of in advance.

- **Input guardrail** — screens every incoming question before it reaches the agent. Rejects prompt injection ("ignore your instructions..."), off-topic requests, and attempts to extract information the agent isn't authorized to share.
- **Output guardrail** — screens the completed answer for ungrounded claims, topic drift, or accidental info leaks, logged for review.
- **Fails open, not closed** — if the judge call itself errors (network blip, rate limit), the system does not silently block legitimate users; it logs the failure and lets the request through. A safety layer that takes down the whole product on its own hiccup is worse than no safety layer.

---

## Evaluation

Ran an LLM-as-judge eval suite across 15 representative queries, scoring **groundedness**, **answer relevance**, and **context relevance** (1–5 scale each).

| Metric | Score |
|---|---|
| Avg. groundedness | **4.4 / 5** |
| Avg. context relevance | **4.6 / 5** |
| Avg. answer relevance | **4.67 / 5** |

**The eval harness had a bug worth documenting, not hiding:** the first run scored groundedness at 3.13/5. Investigation traced it to the eval script calling a *separate* retrieval function with different parameters than the one the agent's own tool actually uses — so the judge was comparing answers against the wrong context window. Fixed by having the eval call the agent's exact `project_retrieval` tool invocation. Corrected score: 4.4/5. Lesson: **always evaluate against the context the system actually used, not a proxy re-retrieval** — a mismatch here silently produces false hallucination reports.

---

## Observability

Every request is traced end-to-end in **LangSmith**: the agent's tool-selection decision, the exact retrieval call and what it returned, the generation step, and full latency/token/cost breakdown per run. This is what makes "it's not a wrapper" a verifiable claim rather than a marketing line — anyone can be shown the actual decision tree for any live request.

**PostHog** tracks real engagement: questions asked, responses completed, resume downloads — separate from LangSmith's technical tracing, this is product-usage analytics.

---

## Performance notes (honest, not cherry-picked)

- Typical end-to-end response time: **~3–5s** for a tool-calling query (retrieval + generation), sub-second for deterministic list queries.
- Root-caused the primary latency source to Qdrant Cloud's free-tier query time (~2–3s of the total) via LangSmith traces — ruled out a suspected Render/Qdrant region mismatch as the cause (moved regions, latency didn't improve, confirming the free-tier vector DB itself was the bottleneck, not geography). Documented rather than papered over, since a real production fix here (dedicated Qdrant tier) is a cost tradeoff, not a code fix.
- Backend runs on Render free tier + a scheduled uptime check to avoid cold-start spin-down.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind, SSE streaming client |
| Backend | FastAPI, LangGraph (ReAct agent), Groq (`openai/gpt-oss-20b`) |
| Retrieval | Qdrant Cloud, fastembed (ONNX, `all-MiniLM-L6-v2`) |
| Guardrails | LLM-as-judge (Groq), input + output screening |
| Observability | LangSmith (tracing), PostHog (analytics) |
| Deployment | Vercel (frontend), Render (backend) |

---

## What's deliberately not built (and why)

- **LiteLLM multi-model gateway** — planned in the original architecture, deprioritized once traffic didn't justify cost-based routing on an already-free Groq tier. Documented as a considered-and-deferred decision, not an oversight.
- **Redis for sessions/logging** — evaluated and skipped: PostHog already covers durable analytics, and a portfolio chat doesn't need cross-visit memory. Building it anyway would have been effort spent on a non-problem.

---

## Run it locally

```bash
# backend
cd askanas-backend
pip install -r requirements.txt
uvicorn app.routes.chat:app --reload

# frontend
cd askanas
npm install
npm run dev
```

Requires `.env` with `GROQ_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `LANGCHAIN_API_KEY` (optional, for tracing).

---

Built and debugged solo by [Anas Khan](https://github.com/Anas2604-web) — [LinkedIn](https://linkedin.com/in/anas-khan-47485224a) · [LeetCode](https://leetcode.com/u/Anas_2604/)

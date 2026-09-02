from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.agent.graph import ask_agent
from app.retrieval.qdrant_store import list_all_projects
import json
import os
from collections import Counter
from datetime import datetime, timezone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    history: list[dict] | None = None

class ChatResponse(BaseModel):
    answer: str

LIST_TRIGGERS = [
    "what projects", "which projects", "all projects",
    "list of projects", "list projects",
    "projects has anas built", "projects has he built",
    "projects anas built", "projects have you built",
]

def is_list_query(question: str) -> bool:
    q = question.lower()
    return any(trigger in q for trigger in LIST_TRIGGERS)

def format_project_list(results: list[dict]) -> str:
    lines = ["Here are all the projects Anas has built:\n"]
    for doc in results:
        title = doc["project_title"]
        first_line = doc["content"].strip().split("\n")[0]
        lines.append(f"- **{title}**: {first_line}")
    lines.append("\nWant me to go deeper on any of these?")
    return "\n".join(lines)

LOG_FILE = "chat_logs.jsonl"

def log_interaction(question: str, answer: str, history: list[dict] | None, error: bool = False):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "history_length": len(history) if history else 0,
        "error": error,
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        print(f"[log_interaction] failed to write log: {e}")

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    error = False
    try:
        if is_list_query(req.question):
            results = list_all_projects()
            answer = format_project_list(results)
        else:
            answer = ask_agent(req.question, req.history)
    except Exception as e:
        print(f"[chat] agent error: {e}")
        answer = "Sorry, something went wrong on my end — try rephrasing or ask again in a moment."
        error = True
    log_interaction(req.question, answer, req.history, error=error)
    return ChatResponse(answer=answer)

@app.get("/metrics")
def metrics():
    """Quick local-dev metrics from chat_logs.jsonl. Not for production use (ephemeral on Render)."""
    if not os.path.exists(LOG_FILE):
        return {"total_questions": 0, "note": "no log file yet"}

    entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    if not entries:
        return {"total_questions": 0}

    total = len(entries)
    errors = sum(1 for e in entries if e.get("error"))
    avg_answer_len = sum(len(e["answer"]) for e in entries) / total
    avg_history_len = sum(e.get("history_length", 0) for e in entries) / total
    question_counts = Counter(e["question"].strip().lower() for e in entries)
    top_questions = question_counts.most_common(10)
    list_query_count = sum(1 for e in entries if is_list_query(e["question"]))

    return {
        "total_questions": total,
        "error_count": errors,
        "error_rate": round(errors / total, 3),
        "avg_answer_length_chars": round(avg_answer_len, 1),
        "avg_history_length": round(avg_history_len, 1),
        "list_query_count": list_query_count,
        "top_questions": top_questions,
        "first_logged": entries[0]["timestamp"],
        "last_logged": entries[-1]["timestamp"],
    }
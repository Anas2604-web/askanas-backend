from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.agent.graph import ask_agent
from app.retrieval.qdrant_store import list_all_projects

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

# Keyword-based intent check for "list all projects" style questions —
# bypasses the LLM's tool-choice judgment for this specific, high-frequency case
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

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    print(f"DEBUG: received question = '{req.question}', is_list_query = {is_list_query(req.question)}")
    if is_list_query(req.question):
        results = list_all_projects()
        answer = format_project_list(results)
    else:
        answer = ask_agent(req.question)
    return ChatResponse(answer=answer)
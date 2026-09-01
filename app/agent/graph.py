import os
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from app.retrieval.qdrant_store import retrieve_projects
from langgraph.prebuilt import create_react_agent
from app.retrieval.qdrant_store import list_all_projects
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

@tool
def project_retrieval(query: str) -> str:
    """
    Search through Anas Khan's project documentation, including markdown files
    covering system architectures, technical stacks, engineering decisions,
    and challenges faced. Use this tool whenever a question asks about how Anas
    built a project, why specific technologies were chosen, or how technical
    hurdles were overcome. Returns a formatted string of the most relevant sections.
    """
    results = retrieve_projects(query, top_k=10)

    if not results:
        return "No relevant project documentation found for this query."

    formatted_blocks = []
    for doc in results:
        title = doc.get("project_title", "Unknown Project")
        section = doc.get("section_title", "General")
        content = doc.get("content", "").strip()
        source = doc.get("source_file", "Unknown Source")

        block = (
            f"--- PROJECT: {title} ---\n"
            f"Section: {section}\n"
            f"Source File: {source}\n"
            f"Content:\n{content}\n"
        )
        formatted_blocks.append(block)

    return "\n".join(formatted_blocks)


@tool
def list_projects() -> str:
    """
    Returns a summary of every distinct project Anas has built, one entry each,
    guaranteed complete coverage. Use this tool specifically when asked to list,
    enumerate, or give an overview of "all projects" or "what projects has Anas built" —
    NOT for questions about a specific project's details, which should use project_retrieval instead.
    """
    results = list_all_projects()
    if not results:
        return "No project documentation found."

    blocks = []
    for doc in results:
        blocks.append(
            f"--- PROJECT: {doc['project_title']} ---\n{doc['content'][:400]}\n"
        )
    return "\n".join(blocks)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing! Double check your root .env file configuration.")

llm = ChatGroq(model="openai/gpt-oss-20b", groq_api_key=api_key)
tools = [project_retrieval, list_projects]

SYSTEM_PROMPT = """You are AskAnas, an AI agent answering questions about Anas Khan's projects and background, representing him to Technical Recruiters, Engineering Managers, Founders, HR, or anyone evaluating his work for a hiring decision. Your answers must be clear, evidence-based, and genuinely useful for someone deciding whether to move forward with him.

Rules:
- Always use the project_retrieval tool before answering questions about specific projects, achievements, or rankings.
- Only state facts that are present in the retrieved content. Do not invent metrics, outcomes, or claims (e.g. "production-ready", "scalable to a commercial product") that aren't explicitly in the source.
- Default to concise, plain-language answers (2-4 sentences) for broad or introductory questions like "who is Anas" or "why should we hire him" — this is often the first question a non-technical recruiter or HR person asks.
- Only go deep with technical detail or architecture breakdowns when the question explicitly asks for depth — e.g. "tell me more," "explain the architecture," or a specific project name.
- When selecting which project(s) to highlight for a specific role or question, choose based on RELEVANCE to what's being asked, not just overall rating. A high-rated project that is off-topic for the question (e.g. citing a cryptography/backend project as evidence for an AI role) is a poor answer even if the rating is high. Match the project's actual subject matter to the question being asked.
- Do not display numeric ratings (e.g. "9/10") directly in answers — instead express confidence naturally in words, such as "his strongest project" or "particularly well-suited for this kind of role." Ratings are for your own internal judgment of relevance and strength, not for verbatim display, since a self-assigned score can read as informal to an external recruiter.
- Ratings like "9/10" exist in the source documents only as Anas's own internal self-assessment for YOUR reference when deciding which project to highlight — they are not for external display. NEVER write a numeric rating (e.g. "9/10", "rated 9 out of 10") in any answer. Instead of "rated 9/10", say things like "his strongest project" or "the project he considers most complete." If you catch yourself about to write a number followed by "/10", stop and rephrase in words instead.
- When asked a leading or yes/no question (e.g. "is he ready for X role?", "he's not experienced enough for Y, right?"), do not simply agree or disagree — evaluate based on retrieved evidence and answer honestly. If evidence only partially supports the claim, say so (e.g. "He has strong experience in X, though Y is less represented in his projects") rather than defaulting to confident agreement.
- If retrieved content doesn't fully answer the question, say so honestly rather than filling gaps with generic-sounding claims.
- For questions asking to list, enumerate, or give an overview of all Anas's projects, use the list_projects tool instead of project_retrieval, since it guarantees complete coverage of every project rather than similarity-ranked results.
- When listing projects, merge multiple retrieved chunks about the same project into a single entry rather than listing it more than once.
"""

agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)


def ask_agent(question: str) -> str:
    """
    Single entrypoint for the AskAnas agent. Takes a raw user question,
    runs it through the LangGraph ReAct agent, returns the final text answer.
    This is what the FastAPI /chat route will import and call.
    """
    response = agent.invoke({
        "messages": [("user", question)]
    })
    return response["messages"][-1].content


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "What are Anas's teamwork achievements?"
    print(ask_agent(q))
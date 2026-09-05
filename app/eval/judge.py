import os, json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
EVAL_MODEL = "openai/gpt-oss-20b"

EVAL_PROMPT = """Evaluate this RAG system's response on three metrics. Respond with ONLY valid JSON:
{{
  "groundedness": 1-5,
  "answer_relevance": 1-5,
  "context_relevance": 1-5,
  "reasoning": "one sentence per metric"
}}

Question: {question}
Retrieved context: {context}
Generated answer: {answer}

Groundedness: does the answer only state things present in the retrieved context?
Answer relevance: does the answer address what was actually asked?
Context relevance: was the retrieved context actually useful for answering this question?
"""

def evaluate_response(question: str, context: str, answer: str) -> dict:
    completion = client.chat.completions.create(
        model=EVAL_MODEL,
        messages=[{"role": "user", "content": EVAL_PROMPT.format(question=question, context=context, answer=answer)}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)
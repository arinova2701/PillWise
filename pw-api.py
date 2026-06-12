import os
import json
import psycopg2
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from pgvector.psycopg2 import register_vector

load_dotenv()

app = FastAPI()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="pillwise",
    user="pillwise",
    password="pillwise123"
)
register_vector(conn)

class Query(BaseModel):
    question: str
    top_k: int = 5

def retrieve(query, top_k=5):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query
    )
    query_embedding = result.embeddings[0].values
    cur = conn.cursor()
    cur.execute("""
        SELECT drug, chunk_text, 1 - (embedding <=> %s::vector) AS similarity
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (query_embedding, query_embedding, top_k))
    return cur.fetchall()

@app.post("/ask")
def ask(query: Query):
    results = retrieve(query.question, query.top_k)
    context = ""
    for i, row in enumerate(results):
        context += f"[{i+1}] ({row[0]}) {row[1]}\n\n"
    prompt = f"""You are a medical information assistant. Answer the question using ONLY the context provided.
For each fact you state, cite the source number in square brackets like [1], [2].
If the context doesn't contain enough information, say so.

Context:
{context}

Question: {query.question}

Answer:"""
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    })
    lines = response.text.strip().split("\n")
    answer = json.loads(lines[0])["response"]
    sources = [{"drug": r[0], "chunk": r[1][:200], "similarity": round(r[2], 4)} for r in results]
    return {"answer": answer, "sources": sources}

@app.get("/health")
def health():
    return {"status": "ok"}
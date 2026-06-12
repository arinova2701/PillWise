# 💊 PillWise

A RAG system for querying FDA drug label information. Ask a question about a medicine and get a cited answer pulled directly from official FDA drug labels.

Built as part of an AI engineering internship assignment focused on RAG pipeline design, vector storage, and LLM integration.

## Stack

| Component       | Tool                                      |
|-----------------|-------------------------------------------|
| Data            | DailyMed FDA drug labels (PDFs)           |
| Embeddings      | Google Gemini (gemini-embedding-001, 3072d)|
| Vector Store    | pgvector + PostgreSQL 16 (Docker)         |
| LLM             | Ollama llama3.2 (local)                   |
| API             | FastAPI                                   |
| Package Manager | uv                                        |

## Project Structure

| File | Description |
|------|-------------|
| `01_scraper.ipynb` | DailyMed automated PDF downloader |
| `02_load_and_chunk.ipynb` | PDF text extraction and chunking strategy comparison |
| `03_embeddings.ipynb` | Gemini embedding pipeline |
| `04_vectorstore.ipynb` | pgvector setup and chunk storage |
| `05_retrieval.ipynb` | Semantic search and answer generation |
| `pw-api.py` | FastAPI REST endpoint |
| `data/raw_pdfs/` | Downloaded drug label PDFs organized by medicine |

## Setup

**Prerequisites:** Docker Desktop, Ollama with llama3.2, uv, Gemini API key (free tier works)

**1. Clone and install**

```bash
git clone https://github.com/arinova2701/PillWise
cd PillWise
uv sync
```

**2. Create a `.env` file in the project root**

```
GEMINI_API_KEY=your_key_here
```

**3. Start pgvector in Docker**

```bash
docker run -d --name pillwise-pgvector -e POSTGRES_USER=pillwise -e POSTGRES_PASSWORD=pillwise123 -e POSTGRES_DB=pillwise -p 5432:5432 pgvector/pgvector:pg16
```

```bash
docker exec -it pillwise-pgvector psql -U pillwise -d pillwise -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**4. Pull llama3.2**

```bash
ollama pull llama3.2
```

**5. Run notebooks 01 through 05 in order** to download PDFs, chunk them, generate embeddings, store in pgvector, and verify retrieval.

**6. Start the API**

```bash
uv run uvicorn pw-api:app --reload
```

API runs at `http://localhost:8000`

## API Reference

**POST /ask**

Send a question and get a cited answer from the drug label corpus.

Request:
```json
{
  "question": "what are the warnings for ibuprofen?",
  "top_k": 5
}
```

Response:
```json
{
  "answer": "The warnings for ibuprofen include cardiovascular thrombotic events [3], gastrointestinal risk including bleeding and ulceration [2], and contraindication in the setting of CABG surgery [3].",
  "sources": [
    {
      "drug": "ibuprofen",
      "chunk": "NSAIDs cause an increased risk of serious gastrointestinal adverse events...",
      "similarity": 0.8159
    }
  ]
}
```

**GET /health**

```json
{"status": "ok"}
```

## How It Works

1. PDFs are downloaded from DailyMed using their public API (3 per medicine, 10 medicines, 30 total)
2. Text is extracted using pymupdf and split into 500 char chunks with 50 char overlap
3. Each chunk is embedded using Gemini producing a 3072 dimensional vector
4. Vectors are stored in pgvector alongside chunk text and metadata
5. At query time, the question is embedded and cosine similarity retrieves the top 5 most relevant chunks
6. Chunks are passed as context to llama3.2 running locally via Ollama
7. The model generates an answer with inline citations referencing source chunks

## Chunking Experiments

Two strategies compared across 30 documents:

| Metric         | Fixed Size | Sentence Based |
|----------------|------------|----------------|
| Total chunks   | 3213       | 1626           |
| Avg chunk size | 497 chars  | 883 chars      |
| Std deviation  | 29         | 499            |
| Min            | 6          | 46             |
| Max            | 500        | 6904           |

Fixed size chunking with overlap performs better for FDA drug labels. Sentence chunking struggles because bullet points lack sentence-ending punctuation, producing chunks up to 6904 characters which are too large for effective retrieval.

## Medicines Covered

acetaminophen, ibuprofen, amoxicillin, metformin, cetirizine, omeprazole, azithromycin, atorvastatin, aspirin, pantoprazole

## Known Limitations

- Free tier Gemini rate limit (100 req/min) slows full embedding. Currently 609 chunks stored covering 3 medicines.
- Bullet characters from PDFs not yet stripped before storage.
- LLM runs locally so response time depends on hardware.

## TODO

- [ ] Insert all 3139 chunks (currently 609 for 3 medicines)
- [ ] Frontend using Lovable
- [ ] Deploy API to Railway
- [ ] Add Indian medicine data via 1mg scraper
- [ ] Clean bullet characters from chunk text
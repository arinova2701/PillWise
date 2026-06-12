```
# PillWise

A RAG system for querying FDA drug label information. Ask a question about a medicine and get a cited answer pulled directly from official FDA drug labels.

Built as part of an AI engineering internship assignment focused on RAG pipeline design, vector storage, and LLM integration.

## Stack

- Data: DailyMed FDA drug labels (PDFs)
- Embeddings: Google Gemini (gemini-embedding-001, 3072 dimensions)
- Vector Store: pgvector + PostgreSQL 16 (Docker)
- LLM: Ollama llama3.2 (runs locally)
- API: FastAPI
- Package Manager: uv

## Project Structure

```
PillWise/
├── 01_scraper.ipynb          # DailyMed automated PDF downloader
├── 02_load_and_chunk.ipynb   # PDF text extraction and chunking strategy comparison
├── 03_embeddings.ipynb       # Gemini embedding pipeline
├── 04_vectorstore.ipynb      # pgvector setup and chunk storage
├── 05_retrieval.ipynb        # Semantic search and answer generation
├── pw-api.py                 # FastAPI REST endpoint
├── data/
│   └── raw_pdfs/             # Downloaded drug label PDFs organized by medicine
│       ├── acetaminophen/
│       ├── ibuprofen/
│       └── ...
├── .env                      # API keys (not committed)
└── pyproject.toml            # uv dependencies
```

## Setup

### Prerequisites

- Docker Desktop
- Ollama with llama3.2 pulled
- uv
- Gemini API key (free tier works)

### 1. Clone the repo

```bash
git clone https://github.com/arinova2701/PillWise
cd PillWise
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

### 4. Start pgvector in Docker

```bash
docker run -d --name pillwise-pgvector -e POSTGRES_USER=pillwise -e POSTGRES_PASSWORD=pillwise123 -e POSTGRES_DB=pillwise -p 5432:5432 pgvector/pgvector:pg16
```

Then enable the vector extension:

```bash
docker exec -it pillwise-pgvector psql -U pillwise -d pillwise -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 5. Pull llama3.2

```bash
ollama pull llama3.2
```

### 6. Run the notebooks in order

Run notebooks 01 through 05 in order to download PDFs, chunk them, generate embeddings, store in pgvector, and verify retrieval.

### 7. Start the API

```bash
uv run uvicorn pw-api:app --reload
```

API runs at `http://localhost:8000`.

## API Reference

### POST /ask

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

### GET /health

```json
{"status": "ok"}
```

## How It Works

1. PDFs are downloaded from DailyMed using their public API (3 PDFs per medicine, 10 medicines, 30 PDFs total)
2. Text is extracted from each PDF using pymupdf and split into 500 character chunks with 50 character overlap
3. Each chunk is embedded using Gemini (gemini-embedding-001) producing a 3072 dimensional vector
4. Vectors are stored in pgvector alongside the chunk text and metadata
5. At query time, the question is embedded and cosine similarity search retrieves the top 5 most relevant chunks
6. The chunks are passed as context to llama3.2 running locally via Ollama
7. The model generates an answer with inline citations referencing the source chunks

## Chunking Experiments

Two chunking strategies were compared across 30 documents:

| metric         | fixed size | sentence based |
|----------------|------------|----------------|
| total chunks   | 3213       | 1626           |
| avg chunk size | 497 chars  | 883 chars      |
| std deviation  | 29         | 499            |
| min            | 6          | 46             |
| max            | 500        | 6904           |

Fixed size chunking with overlap performs better for FDA drug label format. Sentence chunking struggles because bullet points lack sentence-ending punctuation, producing chunks up to 6904 characters which are too large for effective retrieval.

## Medicines Covered

acetaminophen, ibuprofen, amoxicillin, metformin, cetirizine, omeprazole, azithromycin, atorvastatin, aspirin, pantoprazole

## Known Limitations

- Free tier Gemini API rate limit (100 requests/minute) means full embedding takes time. Currently 609 chunks are stored covering 3 medicines.
- Bullet point characters from PDFs are not stripped before storage, which creates some noise in chunks.
- The LLM runs locally so response time depends on your hardware.

## TODO

- [ ] Insert all 3139 chunks (currently 609 for 3 medicines)
- [ ] Frontend using Lovable
- [ ] Deploy API to Railway
- [ ] Add Indian medicine data via 1mg scraper (Selenium with proxy rotation)
- [ ] Strip bullet characters from chunk text before storage

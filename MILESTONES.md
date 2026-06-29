# SynapVault: Development Checkpoints & Milestones

This document outlines the sequential development phases required to achieve a production-ready state for SynapVault. Each phase must be independently tested along with relevant test files stating test case scenarios and verified before proceeding to the next.

---

## Phase 1: Foundation & Skeleton
**Goal:** Establish the underlying infrastructure and ensure frontend and backend can communicate.

### Backend (FastAPI)
* [ ] Initialize Python virtual environment and install core dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `alembic`, `pytest`, `redis`, `celery`).
* [ ] Set up the `docker-compose.yml` to include local Supabase/PostgreSQL and a Redis container for caching and task brokering.
* [ ] Define the base SQLAlchemy 2.0 async engine and database connection dependency.
* [ ] Run `alembic init` and verify the first migration connects to the database.
* [ ] Build a basic `GET /health` endpoint.

### Frontend (Next.js)
* [ ] Initialize Next.js app with TypeScript and Tailwind CSS.
* [ ] Set up a basic layout wrapper (Navbar, Sidebar, Main Content Area).
* [ ] Configure Axios or native `fetch` with the `NEXT_PUBLIC_API_URL` environment variable.

### Test Cases (`test_main.py`)
* **Scenario 1:** `test_health_check_returns_200()` - Verifies the FastAPI server is running and returns a successful JSON payload.
* **Scenario 2:** `test_db_connection_active()` - Asserts that the SQLAlchemy engine successfully pings the local PostgreSQL container.

**Phase 1 End Result:** A fully dockerized PostgreSQL database successfully communicating with a running FastAPI backend, which is successfully serving a health-check payload to the Next.js frontend UI.

---

## Phase 2: The Ingestion Engine
**Goal:** Successfully upload a PDF, parse it, and securely store metadata in PostgreSQL.

### Backend (FastAPI)
* [ ] Create SQLAlchemy models for `User` and `Document`.
* [ ] Generate and apply Alembic migrations for the new tables.
* [ ] Build the `POST /api/v1/documents/upload` endpoint using `UploadFile`.
* [ ] Implement secure file saving (temporarily to local disk or directly to memory).
* [ ] Integrate LangChain's PDF Loader to extract raw text from the uploaded file.
* [ ] Write metadata to the `documents` table and return the new `document_id`.
* [ ] **Efficiency Upgrade:** Configure a Celery worker backed by Redis to handle the heavy PDF parsing and vectorization in the background, freeing up the main FastAPI event loop immediately.

### Frontend (Next.js)
* [ ] Build the Drag-and-Drop file upload component.
* [ ] Implement upload state UI (Progress bar, "Processing" spinner, Success toast).

### Test Cases (`test_ingestion.py`)
* **Scenario 1:** `test_upload_valid_pdf()` - Uploads a dummy PDF and asserts the endpoint returns a `202 Accepted` with a valid `document_id`.
* **Scenario 2:** `test_upload_invalid_filetype()` - Uploads a `.txt` or `.png` file and asserts the API rejects it with a `415 Unsupported Media Type` error.
* **Scenario 3:** `test_document_metadata_saved()` - Queries the test database to ensure the filename and upload status are correctly recorded.

**Phase 2 End Result:** Users can drag and drop a PDF in the UI, watch a loading state, and see a success notification. Behind the scenes, the PDF text is cleanly extracted and the document metadata is securely logged in the database.

---

## Phase 3: Vectorization & Storage
**Goal:** Convert parsed text into vector embeddings and co-locate them with relational data.

### Backend (FastAPI)
* [ ] Update database schema: Enable `pgvector` extension and create the `DocumentChunk` model.
* [ ] Run Alembic migrations to apply vector schema.
* [ ] Integrate LangChain's `RecursiveCharacterTextSplitter` to chunk the raw PDF text.
* [ ] Connect to the Cohere Embed API to generate embeddings for each text chunk.
* [ ] Implement the atomic transaction: Save all chunks and their vectors to the `document_chunks` table using `asyncpg`.

### Test Cases (`test_vectorization.py`)
* **Scenario 1:** `test_text_chunking_logic()` - Passes a known string to LangChain and verifies it splits into the expected number of chunks with correct overlap.
* **Scenario 2:** `test_mock_cohere_embedding()` - Mocks the Cohere Embed API call and verifies the database successfully commits a vector using `pgvector`.
* **Scenario 3:** `test_atomic_transaction_rollback()` - Forces an error halfway through vectorization to verify that no partial document chunks are left behind in the database.

**Phase 3 End Result:** The application autonomously breaks down massive corporate PDFs into semantic blocks, converts them into mathematical vectors via Cohere, and co-locates them alongside user data in PostgreSQL.

---

## Phase 4: RAG Retrieval & AI Synthesis
**Goal:** Perform similarity searches against the vectors and generate accurate answers.

### Backend (FastAPI)
* [ ] Build the `POST /api/v1/chat/query` endpoint.
* [ ] Convert the user's text query into a Cohere embedding.
* [ ] Write the async SQLAlchemy `<->` (cosine distance) query to fetch the top-20 most relevant chunks (Stage 1 Recall).
* [ ] Integrate Cohere Rerank API to score and isolate the top-5 highest relevance chunks (Stage 2 Re-ranking).
* [ ] Construct the LangChain system prompt injected with the retrieved chunk context.
* [ ] Stream the LLM response via Groq API (Llama 3/Mixtral) back to the client.

### Frontend (Next.js)
* [ ] Build the Chat Interface (Input area, message history, user/AI avatars).
* [ ] Implement Zustand to manage the conversational state.
* [ ] Handle the streaming API response to simulate a real-time typing effect.

### Test Cases (`test_retrieval.py`)
* **Scenario 1:** `test_cosine_similarity_search()` - Injects dummy vectors into the test DB and asserts the `pgvector` query correctly returns the top-K closest matches.
* **Scenario 2:** `test_llm_context_injection()` - Verifies the final LangChain prompt accurately contains both the user's question and the retrieved database chunks.

 **Phase 4 End Result:** A seamless, real-time chat interface where the user can query the AI. The AI retrieves context natively from the PostgreSQL vector store and streams back an accurate, hallucination-free answer.

---

## Phase 5: Hardening & Presentation
**Goal:** Ensure the system handles edge cases gracefully and is ready for rollout.

* [ ] **Backend:** Add error handling for Groq/Cohere API rate limits and oversized PDFs.
* [ ] **Backend (Efficiency Upgrade):** Implement Redis caching on the `POST /api/v1/chat/query` endpoint to instantly return answers for previously asked, identical questions to reduce API latency.
* [ ] **Backend (DevOps):** Write a multi-stage Dockerfile for the FastAPI backend to fully containerize the application for production deployment.
* [ ] **Frontend:** Add "Empty States" (what the user sees before uploading a document).
* [ ] **Frontend:** Ensure Tailwind UI is perfectly responsive and visually polished.

### Test Cases (`test_stress_and_edge.py`)
* **Scenario 1:** `test_api_rate_limit_handling()` - Simulates a `429 Too Many Requests` from external APIs (Groq/Cohere) and ensures the backend returns a clean, friendly error to the frontend instead of crashing.
* **Scenario 2:** `test_large_document_load()` - Conducts an end-to-end test pushing a massive, 100+ page corporate document through the ingestion pipeline to monitor memory usage and timeouts.

**Phase 5 End Result:** A polished, robust, production-ready enterprise copilot that looks professional on any device, handles system failures cleanly, and is fully prepared for an executive demo.

---

### FINAL PROJECT OUTCOME
SynapVault is fully operational. The organization now possesses an internal, automated knowledge-retrieval system that cuts document search time from hours to seconds while maintaining strict, verifiable data integrity via PostgreSQL and explicit unit testing.
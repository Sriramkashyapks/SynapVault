# SynapVault: Project Overview & Architecture

## Enterprise Tech Stack & Architecture

### Frontend
* **Next.js (React) & TypeScript:** Server-side rendering and strict type safety for a responsive, reliable UI.
* **Tailwind CSS & Zustand:** Minimalist UI styling and lightweight client-side state management for fluid user experiences.

### Backend (The Async Engine)
* **FastAPI & Uvicorn:** High-performance web framework running on a lightning-fast ASGI server implementation.
* **Pydantic V2:** For strict, compiled request/response data validation and serialization.

### Database & ORM
* **Supabase (PostgreSQL):** Managed Postgres environment providing native support for the `pgvector` extension and granular Row Level Security (RLS).
* **SQLAlchemy 2.0 & asyncpg:** Modern Python ORM utilizing the new 2.0 async paradigm and pooled asynchronous drivers to maximize database throughput.
* **Alembic:** Database migration tool used to track, version, and apply schema changes reliably across environments.

### AI & Orchestration (API-Driven, Low-Cost Strategy)
* **LangChain (Python):** Orchestration framework for document loading, deterministic text chunking (`RecursiveCharacterTextSplitter`), and prompt/context management.
* **Groq Cloud API (Free Tier):** Access to blazing fast Llama 3 or Mixtral models for conversational synthesis, replacing OpenAI to eliminate generation costs.
* **Cohere API:** Advanced semantic re-ranking via Cohere Rerank, and dense vector embeddings via Cohere Embed, leveraging their generous free developer tier.

---

## System Architecture Flow
1. **Asynchronous Ingestion:** A user uploads a dense PDF via the frontend dashboard. FastAPI receives the file payload and immediately fires back a `202 Accepted` status, offloading the expensive processing queue to a background task to avoid connection blocking.
2. **Processing & Chunking:** The background routine invokes LangChain to parse the document text and divide it into overlapping semantic chunks, preserving local context and paragraph cohesion.
3. **Vectorization & Vault Storage:** Chunks are systematically vectorized via the Cohere Embed API. Using `asyncpg` and SQLAlchemy 2.0, the relational metadata and high-dimensional vector embeddings are committed to the Supabase instance inside a single, isolated atomic transaction.
4. **Neural Retrieval & Re-ranking:** When a query is initiated, FastAPI converts it into a query vector, runs an async `<->` (cosine distance) similarity search across the PostgreSQL tables to recall the top 20 relevant chunks. These chunks are then passed through the Cohere Rerank API to accurately identify the top 5 most relevant contexts.
5. **Generation:** The re-ranked top 5 chunks are injected into a LangChain prompt and sent to the Groq API (free tier), which streams the Llama 3/Mixtral model's structured, hallucination-free response back to the client interface.

---

## Core Database Schema (SQLAlchemy Models)

**Model: User (`users`)**
* `id`: UUID (Primary Key, Indexed)
* `email`: String (Unique)
* `created_at`: DateTime (Timezone aware)

**Model: Document (`documents`)**
* `id`: UUID (Primary Key)
* `user_id`: UUID (Foreign Key -> `users.id`, Indexed)
* `filename`: String
* `status`: Enum (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)
* `upload_date`: DateTime

**Model: DocumentChunk (`document_chunks`)**
* `id`: UUID (Primary Key)
* `document_id`: UUID (Foreign Key -> `documents.id`, *Cascade Delete*)
* `chunk_text`: Text
* `embedding`: Vector(1024) (Mapped via `pgvector` to match Cohere's embedding dimensions)

---

## System Design Talking Points
* **Non-Blocking Architecture:** "I specifically selected `asyncpg` alongside SQLAlchemy 2.0's async features. This prevents heavy, data-dense vector similarity searches and external LLM API network hops from bottlenecking the Python ASGI event loop, guaranteeing that SynapVault handles highly concurrent enterprise traffic easily."
* **Production Schema Evolution:** "Instead of performing dangerous manual table alterations, I integrated Alembic. This guarantees that if vector weights shift, dimensions modify, or secondary metadata keys are required, database migrations remain entirely version-controlled, reproducible, and safe to rollback in production."
* **Atomic Pipeline Integrity:** "I designed SynapVault's ingestion framework to guarantee atomicity. Document tracking states and the raw vector chunks are committed in a unified transaction block. If an embedding API limit or failure triggers mid-way through an enterprise manual, the entire transaction rolls back cleanly, avoiding orphaned blocks and table bloat."
* **API-Driven Cost Engineering:** "I designed SynapVault to be model-agnostic and cost-optimized. I decoupled the architecture to use Groq's API for zero-cost generation and Cohere's API for advanced semantic re-ranking. This keeps the infrastructure costs near zero while maintaining enterprise-level RAG accuracy, allowing it to be easily deployed to a basic cloud instance without GPU requirements."
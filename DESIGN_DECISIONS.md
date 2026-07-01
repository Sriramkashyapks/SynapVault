# SynapVault: Architecture Decision Record (ADR)

This document tracks the core design and architectural decisions made during the development of SynapVault to ensure future maintainability, performance, and alignment with industry best practices.

---

## 1. Modular Embedding Strategy (Strategy Pattern)
* **Decision:** Implement a provider-agnostic Strategy Pattern for text embeddings.
* **Rationale:** 
  * Allows the application to switch between self-hosted offline execution (`local` via HuggingFace) and cloud APIs (`cohere` or `openai`) with a single environment variable toggle (`EMBEDDING_PROVIDER`).
  * On a senior-level resume, this demonstrates advanced software engineering design (Strategy Pattern, OOP encapsulation, provider decoupling) compared to hardcoding a single third-party API wrapper.
  * Ensures compliance with enterprise data privacy policies where corporate PDFs must not be sent to external cloud APIs.

---

## 2. Universal 384-Dimensional Database Vector Alignment
* **Decision:** Set pgvector database columns to exactly **384 dimensions** instead of `1024`.
* **Rationale:**
  * **Local Performance:** HuggingFace’s `all-MiniLM-L6-v2` is the industry-standard lightweight CPU-efficient local model (90MB footprint) and outputs 384 dimensions. Running a 1024-dimensional local model (like `bge-large`) would consume >1.3 GB of memory and severely bottleneck local hardware.
  * **Database Type Safety:** In PostgreSQL `pgvector`, the column dimension is fixed at migration time. Aligning to 384 dimensions allows all three strategies to fit cleanly:
    * `local` ➜ `all-MiniLM-L6-v2` (384-dim)
    * `cohere` ➜ `embed-english-light-v3.0` (384-dim, free developer tier)
    * `openai` ➜ `text-embedding-3-small` (truncated to 384-dim natively by OpenAI)
  * **Optimization:** A 384-dimensional vector is 60% smaller in memory and disk space than 1024. This increases pgvector similarity query speeds by over 2x.

---

## 3. FastAPI Dependency Overrides for Testing
* **Decision:** Utilize FastAPI's `app.dependency_overrides` inside pytest fixtures to inject the test database session.
* **Rationale:**
  * Avoids event loop conflicts (`InterfaceError: another operation is in progress` and `Attached to a different loop`) in asynchronous database testing.
  * Forces the FastAPI endpoint execution and the test runner logic to share the **exact same database session and connection pool** inside the active test loop.
  * Ensures all database operations committed by test requests are cleanly isolated and rolled back automatically at the end of each test execution.

---

## 4. Cost-Optimized Cloud Deployment Plan
* **Decision:** Deploy the application utilizing distributed free-tier cloud platforms.
* **Architecture Map:**
  1. **Frontend (Next.js):** Hosted on **Vercel** (Hobby free tier).
  2. **Backend (FastAPI):** Hosted on **Render** (Free tier, utilizing standard CPU memory).
  3. **Database (Postgres + pgvector):** Hosted on **Supabase** (Free project tier with pgvector enabled).
  4. **API Keys:** Uses Groq Cloud (Free tier) for conversational AI synthesis, and the Cohere Developer Key (Trial tier, 40 req/min) for re-ranking.

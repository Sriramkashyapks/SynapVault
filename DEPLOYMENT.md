# SynapVault: Deployment Strategy & Architecture

This document outlines the deployment strategy for SynapVault, detailing how the architecture transitions from a local development environment to a production-ready cloud deployment while maintaining a **100% Free / Cost-Optimized** footprint.

> [!NOTE]  
> **Production & API Usage:** While the underlying codebase and architecture are highly optimized and fully compatible with production environments, the default setup relies on free-tier APIs primarily for learning and demonstration purposes. For actual enterprise deployments, it is highly recommended to procure paid API keys for your preferred LLM and embedding providers to achieve better rate limits, reliability, and results.

---

## 1. Local Development Architecture

During the development phase, we prioritize speed, offline capability, and zero reliance on managed cloud infrastructure where possible.

* **Frontend:** Next.js development server (`npm run dev`) running locally on port 3000.
* **Backend:** FastAPI ASGI server (`uvicorn`) running locally on port 8000.
* **Database & Task Broker (Dockerized):**
  * **PostgreSQL (with `pgvector`):** Hosted via a local `docker-compose.yml` file to test schema migrations and vector similarity searches offline.
  * **Redis:** Hosted via the same `docker-compose.yml` to act as the Celery task broker for background PDF parsing and endpoint caching.
* **External APIs (The only external hops):**
  * Groq Cloud API for LLM generation.
  * Cohere API for embeddings and semantic re-ranking.

---

## 2. Production Cloud Architecture

When deploying to production, we decouple the infrastructure into specialized microservices. This guarantees scalability and keeps the system within generous free-tier limits without relying on a single expensive server.



### Frontend: Vercel
* **Role:** Hosts the Next.js static assets and server-side rendered pages.
* **Cost:** 100% Free on the hobby tier.
* **Configuration:** Automatically deploys from the GitHub main branch. Connects to the Render backend via the `NEXT_PUBLIC_API_URL` environment variable.

### Backend: Render
* **Role:** Hosts the FastAPI ASGI web server and the Celery worker process.
* **Cost:** 100% Free on the Web Services free tier.
* **Configuration:** Pulls the multi-stage Docker container (or native Python environment). Connects to Supabase and Upstash via environment variables.

### Database: Supabase
* **Role:** Managed PostgreSQL environment providing native support for the `pgvector` extension.
* **Cost:** 100% Free on the active project tier.
* **Configuration:** Replaces the local Dockerized Postgres. Connection string is provided to Render as `DATABASE_URL`.

### Task Broker & Cache: Upstash (Serverless Redis)
* **Role:** Replaces the local Dockerized Redis. Handles the Celery background task queue and caches identical LLM queries to reduce latency.
* **Cost:** 100% Free on the generous developer tier.
* **Configuration:** Connection string is provided to Render as `REDIS_URL`.

---

## System Design Benefits

This deployment strategy leverages advanced system design principles to ensure scalability and maintainability:
1. **Microservices & Decoupling:** Instead of consolidating the database, web server, and cache onto a single virtual machine, the architecture utilizes specialized, purpose-built platforms for optimal performance.
2. **Cost Engineering:** Infrastructure hosting costs are minimized by designing the system to operate efficiently within distributed, free-tier managed services (Vercel, Render, Supabase, and Upstash).
3. **Environment Parity:** The architecture maintains a clear separation between local containerized workflows (Docker) and production managed services, adhering to modern DevOps best practices.

---

## 3. Environment Configuration

To run and deploy the backend, configure the following environment variables (defined in your local `.env` or in the Render/Supabase cloud dashboards):

* `DATABASE_URL`: Asynchronous connection string to your PostgreSQL database.
* `REDIS_URL`: Connection string to your Redis cache/broker instance.
* `EMBEDDING_PROVIDER`: The active embedding strategy (`local` for self-hosted HF models, `cohere` for cloud Cohere embeddings, or `openai` for cloud OpenAI embeddings).
* `COHERE_API_KEY`: API key for Cohere (optional, required if `EMBEDDING_PROVIDER=cohere`).
* `OPENAI_API_KEY`: API key for OpenAI (optional, required if `EMBEDDING_PROVIDER=openai`).


# SynapVault Backend — Developer Guidelines

These guidelines ensure a clean, high-performance, and scalable FastAPI backend, adopting enterprise patterns without overengineering.

---

## 1. Naming Conventions

| What | Case | Example |
| --- | --- | --- |
| Files & Directories | `snake_case.py` | `document_parser.py` |
| Classes (Models/Schemas) | `PascalCase` | `DocumentChunk` |
| Functions & Variables | `snake_case` | `extract_pdf_text()` |
| Constants | `SCREAMING_SNAKE_CASE`| `MAX_FILE_SIZE_MB` |

---

## 2. Project Structure & Architecture

Keep concerns strictly separated to ensure maintainability:

* `routers/` — FastAPI endpoint definitions (`@router.get(...)`). **Keep them thin.** Routers should just call a service and return the response.
* `services/` — Core business logic.
* `models/` — SQLAlchemy database tables.
* `schemas/` — Pydantic models.
* `core/` — App configuration, settings, and security dependencies.

**Direction:** `Router -> Service -> Model (Database)`. Never reverse.

---

## 3. Validation & Error Handling

* **Pydantic Everywhere:** Never accept raw JSON. Always validate incoming data via a Pydantic `BaseModel` schema.
* **Standardized Errors:** Have a consistent response format for errors, rather than throwing random exceptions. Example:
  ```json
  {
    "success": false,
    "message": "...",
    "error_code": 400
  }
  ```

---

## 4. Database & ORM

* **Asynchronous ORM:** Use `asyncpg` and SQLAlchemy 2.0 with `async def` and `AsyncSession`.
* **Migrations:** Never manually alter a table. Always use Alembic.
* **Atomic Transactions:** Related database operations should be wrapped in a single transaction to preserve data consistency.

---

## 5. Background Tasks & Performance

* **Asynchronous Processing:** Heavy processing (like parsing PDFs) should be asynchronous. Use FastAPI `BackgroundTasks` during development, and only migrate to Celery when distributed workers or retries become necessary.
* **Caching:** Use Redis caching where it solves a measured performance problem (e.g., chat cache, rate limiting, session storage) rather than overengineering vector caching by default.

---

## 6. Development Quality

* **Logging:** Never use `print()`. Use Python's built-in `logging` module or `loguru` for robust logs.
* **Environment Separation:** Maintain clear separation using `.env`, `.env.example`, and `.env.production`.
* **Linting & Formatting:** Enforce clean code using `ruff` and `black`.
* **Testing:** Critical business logic and core APIs should have tests. For a solo project, aim for practical coverage over 100% test coverage.

---

## 7. Pre-Push Checklist

- [ ] Routers are thin and logic resides in services.
- [ ] No raw `print()` statements; proper logging is used.
- [ ] Critical APIs have basic `pytest` coverage.
- [ ] Code is linted with `ruff`/`black`.

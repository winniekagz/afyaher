AfyaHer — GitHub Copilot Instructions
This repository builds a private, mobile-first reproductive-health education prototype, not a diagnostic or clinically approved medical product.

Read CLAUDE.md before making substantial changes. Follow the product, architecture, safety, privacy, and testing rules there. Also read docs/PRD.md, docs/ARCHITECTURE.md, and docs/SYSTEM_DESIGN.md when available. Do not assume missing files exist.

Core stack: Next.js + TypeScript frontend; FastAPI + Python backend; PostgreSQL + pgvector; Pydantic; SQLAlchemy/Alembic; pytest, Vitest, Playwright. FastAPI owns RAG, safety checks, source provenance, citation validation, and AI provider calls.

Work in small testable vertical slices. Never add diagnosis, treatment advice, medical-record uploads, chat persistence, invented citations, unreviewed content to production retrieval, or unapproved architecture changes. Use synthetic medical scenarios. Never commit API keys. Ask for approval before dependencies, migrations, destructive actions, or scope expansion.

Subsequent MVP milestone: a single PCOS educational question answered with verifiable source citations through Next.js -> FastAPI -> retrieval -> model -> validation. Do not mark medical safety as clinically validated.

Day 1 implementation agreement (approved)
The immediate milestone is GET /api/v1/health plus a Next.js connectivity page with loading, success, and error states. The PCOS educational slice remains the subsequent MVP goal. Use npm for frontend dependencies and uv for backend dependencies. Keep development local, private, adults-only, and synthetic. Do not add medical advice, RAG, AI generation, authentication, or database infrastructure on Day 1. Approval for this Day 1 scope and its proposed dependencies has already been given; proceed incrementally without requesting the same approval again. Missing PRD, architecture, and system design documents must be reported, never represented as existing approved specifications. Preserve existing Git history.

Engineering standards: Follow all engineering, medical safety, privacy, evidence, and verification rules in CLAUDE.md; they apply equally to Copilot. Use typed request/response contracts, thin FastAPI routes, runtime validation at API boundaries, accessible UI, and meaningful success/failure tests. Never persist health questions or expose secrets to client bundles. Report actual checks and limitations.

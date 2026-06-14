# AGENTS.md

## Project context

This is a portfolio backend project for a self-taught Junior Backend Developer.

Project name:
Task Manager API

Main goal:
Build a production-quality FastAPI backend that can be shown to employers.

## Tech stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Alembic
- JWT authentication
- Docker
- Pytest

## Development rules

- Do not rewrite the entire project unless explicitly requested.
- Make small, focused changes.
- Explain the reason for every architectural decision.
- Preserve the current project structure when possible.
- Use type hints.
- Follow PEP8.
- Avoid quick hacks.
- Do not commit secrets.
- Do not hardcode passwords, tokens, API keys, or database URLs.
- Use environment variables for configuration.
- Keep business logic separate from API routes.
- Prefer maintainable code over clever code.

## Current priorities

1. Fix password hashing.
2. Move configuration to environment variables.
3. Implement reliable user registration.
4. Add login with JWT.
5. Add task CRUD.
6. Add Alembic migrations.
7. Add Docker and tests.

## Review guidelines

- Check for security issues.
- Check for hardcoded secrets.
- Check authentication and authorization logic.
- Check error handling.
- Check database session handling.
- Check whether the code is understandable for a Junior Developer.
# Project Context

We are building a professional backend portfolio project.

Repository:
https://github.com/Unequal1213/task-manager-api

Project:
Task Manager API

Current status:

- FastAPI app is created.
- PostgreSQL is installed locally.
- pgAdmin is working.
- Database `task_manager_db` exists.
- SQLAlchemy is configured.
- User model exists.
- `users` table exists in PostgreSQL.
- `/register` endpoint exists.
- Swagger UI works at `http://127.0.0.1:8000/docs`.

Current problem:

Registration fails during password hashing because of compatibility issues between passlib, bcrypt, and the current Python environment.

Current files:

- app/main.py
- app/api/auth.py
- app/core/security.py
- app/database/database.py
- app/models/user.py
- app/schemas/user.py

Important:

- Do not hardcode secrets.
- Move database URL to `.env`.
- Use clean architecture gradually.
- Do not rewrite the entire project.
# Task Manager API

FastAPI backend using PostgreSQL, SQLAlchemy, JWT authentication, and
Alembic migrations.

## Local Development

Create a local `.env` file from `.env.example` and replace all placeholder
values. The `.env` file is ignored by both Git and Docker.

Install runtime dependencies and start the API:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

Install development and testing dependencies. This also installs the runtime
dependencies because `requirements-dev.txt` includes `requirements.txt`:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run tests locally:

```powershell
.\venv\Scripts\python.exe -m pytest
```

Run Ruff linting locally:

```powershell
.\venv\Scripts\python.exe -m ruff check .
```

## Database Migrations

Set `DATABASE_URL` in the local `.env` file. Alembic loads the same
environment-based database configuration as the application; database
credentials are not stored in `alembic.ini`.

Apply all migrations to a new database:

```powershell
.\venv\Scripts\alembic.exe upgrade head
```

After changing a SQLAlchemy model, generate a migration:

```powershell
.\venv\Scripts\alembic.exe revision --autogenerate -m "describe the change"
```

Review every generated migration, then apply it:

```powershell
.\venv\Scripts\alembic.exe upgrade head
```

Check the current migration state:

```powershell
.\venv\Scripts\alembic.exe current
.\venv\Scripts\alembic.exe history
```

### Existing Local Database

If `users` and `tasks` were already created manually and match the initial
migration, record that migration without recreating the tables:

```powershell
.\venv\Scripts\alembic.exe stamp head
```

Use `stamp` only for an existing matching schema. New or empty databases
should use `upgrade head`.

The old `create_db.py` workflow has been removed. Do not call
`Base.metadata.create_all()` during application startup; schema changes are
managed through Alembic.

## Docker

Docker Compose runs the FastAPI application and PostgreSQL in separate
containers. PostgreSQL data is stored in the named `postgres_data` volume.

1. Create `.env` from `.env.example`.
2. Replace `POSTGRES_PASSWORD` and `JWT_SECRET_KEY` with secure values.
3. Start the stack:

Generate URL-safe random values without storing them in source code:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Run the command separately for the database password and JWT secret. Docker
Compose reads these values from the ignored `.env` file. It constructs the
container `DATABASE_URL` with the internal hostname `postgres`; the local
`DATABASE_URL` remains available for running the API outside Docker.

```powershell
docker compose up --build
```

The API is available at `http://127.0.0.1:8000`, or at the port configured
by `APP_PORT`. Swagger UI is available at `/docs`.

The application container waits for PostgreSQL to become healthy, runs
`alembic upgrade head`, and then starts Uvicorn. Migrations can also be run
manually inside Docker:

```powershell
docker compose run --rm app alembic upgrade head
docker compose run --rm app alembic current
docker compose run --rm app alembic history
```

Generate a migration after changing SQLAlchemy models:

```powershell
docker compose run --rm app alembic revision --autogenerate -m "describe change"
```

Generated migration files are created inside the temporary container. To
keep a newly generated file on the host, run the command with a bind mount:

```powershell
docker compose run --rm --volume "${PWD}:/app" app alembic revision --autogenerate -m "describe change"
```

Stop the containers while preserving database data:

```powershell
docker compose down
```

Delete the containers and PostgreSQL volume:

```powershell
docker compose down --volumes
```

The last command permanently deletes the Docker database. The real `.env`
file is excluded from the build context and must never be committed.

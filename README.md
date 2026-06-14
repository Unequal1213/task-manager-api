# Task Manager API

FastAPI backend using PostgreSQL, SQLAlchemy, JWT authentication, and
Alembic migrations.

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

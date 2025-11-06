# Alembic Migrations

- Run `alembic -c anything-agents/alembic.ini upgrade head` to apply migrations.
- Generate a new migration with `alembic -c anything-agents/alembic.ini revision -m "message"`.
- Configure the target database URL via `DATABASE_URL` (see `app/core/config.py`).

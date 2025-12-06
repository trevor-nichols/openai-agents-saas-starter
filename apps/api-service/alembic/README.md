# Alembic Migrations

- Run `alembic -c api-service/alembic.ini upgrade head` to apply migrations.
- Generate a new migration with `alembic -c api-service/alembic.ini revision -m "message"`.
- Configure the target database URL via `DATABASE_URL` (see `app/core/settings/__init__.py`).

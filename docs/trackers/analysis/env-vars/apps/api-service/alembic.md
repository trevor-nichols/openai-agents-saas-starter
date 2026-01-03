## apps/api-service/alembic

**Notes**: Note that while the variable is not explicitly read via `os.environ` in `env.py`, the code explicitly enforces its existence via a settings object and references the variable name in a required configuration error message.

| Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DATABASE_URL** | Configures the database connection URL for Alembic migrations. | `env.py`: `get_database_url` (referenced in validation error message, lines 43-45) | Yes | None | String (SQLAlchemy URL) | Secret |
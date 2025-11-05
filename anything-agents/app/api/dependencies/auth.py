"""Authentication-related dependency helpers for API routers."""

from fastapi import Depends

from app.core.security import get_current_user


CurrentUser = dict[str, object]


async def require_current_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Enforce authentication and expose the current user payload."""

    return user

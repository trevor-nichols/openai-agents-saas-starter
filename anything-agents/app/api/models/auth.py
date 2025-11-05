"""Authentication request and response models."""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT access token payload returned to clients."""

    access_token: str = Field(description="Signed JWT access token.")
    token_type: str = Field(
        default="bearer",
        description="Token type hint for the Authorization header.",
    )
    expires_in: int = Field(
        description="Token expiration time expressed in seconds.",
    )


class TokenData(BaseModel):
    """JWT claims used internally once a token is validated."""

    user_id: str = Field(description="Authenticated user identifier.")


class UserLogin(BaseModel):
    """User login credentials."""

    username: str = Field(description="Username or email.")
    password: str = Field(description="User password.")


class UserCreate(BaseModel):
    """User registration payload."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Desired username.",
    )
    email: EmailStr = Field(description="User email address.")
    password: str = Field(
        min_length=8,
        description="Plaintext password to be hashed.",
    )


class UserResponse(BaseModel):
    """User payload returned by user-related endpoints."""

    id: str = Field(description="User identifier.")
    username: str = Field(description="Username.")
    email: str = Field(description="User email address.")
    is_active: bool = Field(description="Whether the user is active.")
    created_at: str = Field(description="Creation timestamp.")

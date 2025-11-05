# File: app/schemas/auth.py
# Purpose: Authentication Pydantic schemas for anything-agents
# Dependencies: pydantic
# Used by: auth routers for request/response validation

from pydantic import BaseModel, Field, EmailStr

# =============================================================================
# TOKEN SCHEMAS
# =============================================================================

class Token(BaseModel):
    """JWT token response schema."""
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")

class TokenData(BaseModel):
    """Token data schema for internal use."""
    
    user_id: str = Field(description="User ID")

# =============================================================================
# USER SCHEMAS
# =============================================================================

class UserLogin(BaseModel):
    """User login request schema."""
    
    username: str = Field(description="Username or email")
    password: str = Field(description="User password")

class UserCreate(BaseModel):
    """User creation request schema."""
    
    username: str = Field(min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(description="User email")
    password: str = Field(min_length=8, description="User password")

class UserResponse(BaseModel):
    """User response schema (without password)."""
    
    id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="User email")
    is_active: bool = Field(description="User active status")
    created_at: str = Field(description="User creation timestamp") 
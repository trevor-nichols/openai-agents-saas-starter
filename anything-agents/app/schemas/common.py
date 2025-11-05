# File: app/schemas/common.py
# Purpose: Common Pydantic schemas for anything-agents
# Dependencies: pydantic
# Used by: API routers for request/response validation

from typing import Optional, Any
from pydantic import BaseModel, Field

# =============================================================================
# COMMON RESPONSE SCHEMAS
# =============================================================================

class SuccessResponse(BaseModel):
    """Standard success response schema."""
    
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(description="Success message")
    data: Optional[Any] = Field(default=None, description="Response data")

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Any] = Field(default=None, description="Error details")

class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(description="Service status")
    timestamp: str = Field(description="Health check timestamp")
    version: str = Field(description="Service version")
    uptime: Optional[float] = Field(default=None, description="Service uptime in seconds")

# =============================================================================
# PAGINATION SCHEMAS
# =============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters schema."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    
    items: list = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page") 
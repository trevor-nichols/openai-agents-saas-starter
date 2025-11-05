# File: app/routers/api.py
# Purpose: Main API endpoints for anything-agents
# Dependencies: fastapi, app/schemas/common
# Used by: Frontend applications for business logic

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.schemas.common import SuccessResponse, PaginationParams, PaginatedResponse
from app.core.security import get_current_user

router = APIRouter()

# Demo data for example endpoints
demo_items = [
    {"id": i, "name": f"Item {i}", "description": f"Description for item {i}"}
    for i in range(1, 51)  # 50 demo items
]

@router.get("/items", response_model=PaginatedResponse)
async def get_items(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term")
):
    """Get paginated list of items."""
    
    # Filter items based on search term
    filtered_items = demo_items
    if search:
        filtered_items = [
            item for item in demo_items 
            if search.lower() in item["name"].lower() or 
               search.lower() in item["description"].lower()
        ]
    
    # Calculate pagination
    total = len(filtered_items)
    start = (page - 1) * limit
    end = start + limit
    items = filtered_items[start:end]
    
    pages = (total + limit - 1) // limit
    has_next = page < pages
    has_prev = page > 1
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/items/{item_id}", response_model=SuccessResponse)
async def get_item(item_id: int):
    """Get a specific item by ID."""
    
    item = next((item for item in demo_items if item["id"] == item_id), None)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return SuccessResponse(
        message="Item retrieved successfully",
        data=item
    )

@router.post("/items", response_model=SuccessResponse)
async def create_item(
    item_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new item (requires authentication)."""
    
    # In a real application, you would validate the item_data
    # and save it to a database
    
    new_item = {
        "id": len(demo_items) + 1,
        "name": item_data.get("name", "New Item"),
        "description": item_data.get("description", "New item description"),
        "created_by": current_user["user_id"]
    }
    
    return SuccessResponse(
        message="Item created successfully",
        data=new_item
    ) 
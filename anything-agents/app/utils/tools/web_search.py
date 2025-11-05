# File: app/utils/tools/web_search.py
# Purpose: Web search tools using Tavily API for anything-agents
# Dependencies: tavily-python, agents, app/core/config
# Used by: Agent service for web search functionality

import asyncio
from typing import Optional, List, Dict, Any
from tavily import TavilyClient
from agents import function_tool
from app.core.config import get_settings

# =============================================================================
# TAVILY CLIENT INITIALIZATION
# =============================================================================

def get_tavily_client() -> Optional[TavilyClient]:
    """
    Get Tavily client instance.
    
    Returns:
        Optional[TavilyClient]: Tavily client if API key is available, None otherwise
    """
    settings = get_settings()
    
    if not hasattr(settings, 'tavily_api_key') or not settings.tavily_api_key:
        return None
    
    return TavilyClient(api_key=settings.tavily_api_key)

# =============================================================================
# WEB SEARCH TOOLS
# =============================================================================

@function_tool
async def tavily_search_tool(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = True,
    topic: str = "general"
) -> str:
    """
    Search the web using Tavily API for current information.
    
    This tool allows agents to search the web for real-time information,
    current events, facts, and any topic that requires up-to-date data.
    
    Args:
        query: The search query to execute
        max_results: Maximum number of search results (1-20, default: 5)
        search_depth: Search depth - "basic" or "advanced" (default: "basic")
        include_answer: Whether to include an AI-generated answer (default: True)
        topic: Search topic - "general" or "news" (default: "general")
    
    Returns:
        str: Formatted search results with sources and optional AI answer
    """
    
    # Get Tavily client
    client = get_tavily_client()
    if not client:
        return "Web search is not available. Tavily API key is not configured."
    
    try:
        # Validate parameters
        max_results = max(1, min(20, max_results))
        search_depth = search_depth if search_depth in ["basic", "advanced"] else "basic"
        topic = topic if topic in ["general", "news"] else "general"
        
        # Execute search
        response = await asyncio.to_thread(
            client.search,
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
            topic=topic,
            include_raw_content=False,
            include_images=False
        )
        
        # Format results
        formatted_results = _format_search_results(response, query)
        return formatted_results
        
    except Exception as e:
        return f"Web search failed: {str(e)}"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_search_results(response: Dict[str, Any], query: str) -> str:
    """
    Format Tavily search results into a readable string.
    
    Args:
        response: Raw Tavily API response
        query: Original search query
        
    Returns:
        str: Formatted search results
    """
    
    formatted = f"🔍 Web Search Results for: '{query}'\n"
    formatted += "=" * 50 + "\n\n"
    
    # Add AI-generated answer if available
    if response.get("answer"):
        formatted += "📝 AI Summary:\n"
        formatted += f"{response['answer']}\n\n"
        formatted += "📚 Sources:\n"
        formatted += "-" * 20 + "\n"
    
    # Add search results
    results = response.get("results", [])
    if not results:
        formatted += "No search results found.\n"
        return formatted
    
    for i, result in enumerate(results, 1):
        title = result.get("title", "No title")
        url = result.get("url", "No URL")
        content = result.get("content", "No content available")
        score = result.get("score", 0)
        
        formatted += f"{i}. {title}\n"
        formatted += f"   URL: {url}\n"
        formatted += f"   Relevance: {score:.2f}\n"
        formatted += f"   Content: {content[:200]}{'...' if len(content) > 200 else ''}\n\n"
    
    # Add metadata
    response_time = response.get("response_time", "Unknown")
    formatted += f"⏱️ Search completed in {response_time} seconds\n"
    
    return formatted 
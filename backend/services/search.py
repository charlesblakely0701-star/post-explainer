"""Search service for fetching context from the web."""

import httpx
from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from models.schemas import SearchResult
from config import get_settings

logger = logging.getLogger(__name__)


class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute a search query and return results."""
        pass


class TavilySearchProvider(SearchProvider):
    """Tavily AI search provider - optimized for AI agents."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Search using Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        settings = get_settings()
        
        async with httpx.AsyncClient(timeout=settings.search_timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_answer": False,
                        "include_raw_content": False,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", "")[:500],  # Truncate long snippets
                        score=item.get("score")
                    ))
                
                return results
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Tavily API error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.TimeoutException:
                logger.error(f"Tavily API timeout for query: {query}")
                raise
            except Exception as e:
                logger.error(f"Tavily search error: {str(e)}")
                raise


class BraveSearchProvider(SearchProvider):
    """Brave Search API provider - fallback option."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1"
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Search using Brave Search API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        settings = get_settings()
        
        async with httpx.AsyncClient(timeout=settings.search_timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/web/search",
                    headers={
                        "X-Subscription-Token": self.api_key,
                        "Accept": "application/json",
                    },
                    params={
                        "q": query,
                        "count": max_results,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("web", {}).get("results", []):
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", "")[:500],
                    ))
                
                return results
                
            except Exception as e:
                logger.error(f"Brave search error: {str(e)}")
                raise


class SearchService:
    """
    Main search service that orchestrates search providers.
    Includes fallback logic and deduplication.
    """
    
    def __init__(self):
        settings = get_settings()
        self.primary_provider = TavilySearchProvider(settings.tavily_api_key)
        
        # Optional fallback provider
        self.fallback_provider: Optional[SearchProvider] = None
        if settings.brave_api_key:
            self.fallback_provider = BraveSearchProvider(settings.brave_api_key)
    
    async def search(self, queries: List[str], max_results_per_query: int = 5) -> List[SearchResult]:
        """
        Execute multiple search queries and return deduplicated results.
        
        Args:
            queries: List of search queries
            max_results_per_query: Max results per query
            
        Returns:
            Deduplicated list of SearchResult objects
        """
        all_results = []
        
        for query in queries:
            try:
                results = await self.primary_provider.search(query, max_results_per_query)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Primary search failed for '{query}': {e}")
                
                # Try fallback if available
                if self.fallback_provider:
                    try:
                        results = await self.fallback_provider.search(query, max_results_per_query)
                        all_results.extend(results)
                    except Exception as fallback_error:
                        logger.error(f"Fallback search also failed: {fallback_error}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Sort by score if available, otherwise keep original order
        unique_results.sort(key=lambda x: x.score or 0, reverse=True)
        
        settings = get_settings()
        return unique_results[:settings.max_search_results]


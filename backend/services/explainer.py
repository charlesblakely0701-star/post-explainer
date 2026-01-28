"""Main orchestration service for post explanation."""

import re
from typing import AsyncGenerator, Optional, Dict, Any
import logging

from models.schemas import ExplainResponse, Source, SearchResult
from services.search import SearchService
from services.llm import LLMService
from services.query_extractor import extract_search_queries
from services.cache import CacheService
from services.image_processor import ImageProcessor
from prompts import build_explanation_prompt

logger = logging.getLogger(__name__)


class PostExplainer:
    """
    Main service that orchestrates the explanation pipeline.
    
    Pipeline:
    1. Check cache
    2. Extract search queries from post
    3. Execute searches
    4. Optionally process image
    5. Generate explanation with LLM
    6. Parse and format response
    7. Cache result
    """
    
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        self.cache_service = CacheService()
        self.image_processor = ImageProcessor()
    
    async def explain(
        self, 
        post_text: str, 
        image_url: Optional[str] = None,
        use_cache: bool = True
    ) -> ExplainResponse:
        """
        Generate an explanation for a social media post.
        
        Args:
            post_text: The post text to explain
            image_url: Optional URL to an image in the post
            use_cache: Whether to check/use cache
            
        Returns:
            ExplainResponse with bullets and sources
        """
        # Check cache first
        cache_key = f"{post_text}:{image_url or ''}"
        if use_cache:
            cached = self.cache_service.get(cache_key)
            if cached:
                return ExplainResponse(
                    bullets=cached["bullets"],
                    sources=[Source(**s) for s in cached["sources"]],
                    cached=True
                )
        
        # Process image if provided
        image_data = None
        if image_url:
            logger.info(f"Processing image: {image_url}")
            image_data = await self.image_processor.prepare_image_for_vision(image_url)
            if image_data:
                logger.info("Image processed successfully for vision")
            else:
                logger.warning("Failed to process image, continuing without it")
        
        # Extract search queries
        queries = extract_search_queries(post_text)
        logger.info(f"Generated {len(queries)} search queries: {queries}")
        
        # Execute searches
        search_results = await self.search_service.search(queries)
        logger.info(f"Got {len(search_results)} search results")
        
        # Build prompt and generate explanation
        prompt = build_explanation_prompt(post_text, search_results)
        raw_response = await self.llm_service.generate(prompt, image_data)
        
        # Parse response into bullets
        bullets = self._parse_bullets(raw_response)
        
        # Build sources list
        sources = self._build_sources(search_results, raw_response)
        
        # Create response
        response = ExplainResponse(
            bullets=bullets,
            sources=sources,
            cached=False
        )
        
        # Cache the result
        if use_cache:
            self.cache_service.set(cache_key, {
                "bullets": bullets,
                "sources": [s.model_dump() for s in sources]
            })
        
        return response
    
    async def compare_providers(
        self,
        post_text: str,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate explanations from multiple providers for comparison.
        
        Args:
            post_text: The post text to explain
            image_url: Optional image URL
            
        Returns:
            Dict with provider names mapping to their responses
        """
        # Process image if provided
        image_data = None
        if image_url:
            image_data = await self.image_processor.prepare_image_for_vision(image_url)
        
        # Extract search queries and get results
        queries = extract_search_queries(post_text)
        search_results = await self.search_service.search(queries)
        
        # Build prompt
        prompt = build_explanation_prompt(post_text, search_results)
        
        # Get responses from all providers
        provider_responses = await self.llm_service.compare_providers(prompt, image_data)
        
        # Parse responses
        results = {}
        for provider_name, raw_response in provider_responses.items():
            if raw_response.startswith("Error:"):
                results[provider_name] = {
                    "error": raw_response,
                    "bullets": [],
                    "sources": []
                }
            else:
                bullets = self._parse_bullets(raw_response)
                sources = self._build_sources(search_results, raw_response)
                results[provider_name] = {
                    "bullets": bullets,
                    "sources": [s.model_dump() for s in sources]
                }
        
        return {
            "providers": results,
            "available_providers": self.llm_service.get_available_providers()
        }
    
    async def explain_stream(
        self, 
        post_text: str
    ) -> AsyncGenerator[dict, None]:
        """
        Stream an explanation for a social media post.
        
        Args:
            post_text: The post text to explain
            
        Yields:
            Dict with event type and data
        """
        # Extract search queries
        queries = extract_search_queries(post_text)
        logger.info(f"Generated {len(queries)} search queries: {queries}")
        
        # Execute searches
        search_results = await self.search_service.search(queries)
        logger.info(f"Got {len(search_results)} search results")
        
        # Yield sources first
        sources = [
            {
                "id": i + 1,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet[:200] if r.snippet else None
            }
            for i, r in enumerate(search_results)
        ]
        yield {"type": "sources", "data": sources}
        
        # Build prompt and stream explanation
        prompt = build_explanation_prompt(post_text, search_results)
        
        async for chunk in self.llm_service.stream(prompt):
            yield {"type": "chunk", "data": chunk}
    
    def _parse_bullets(self, raw_response: str) -> list[str]:
        """
        Parse bullet points from LLM response.
        
        Args:
            raw_response: Raw LLM output
            
        Returns:
            List of bullet point strings
        """
        bullets = []
        
        # Split by bullet markers (•, -, *, or numbered)
        lines = raw_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Remove common bullet markers
            cleaned = re.sub(r'^[•\-\*]\s*', '', line)
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            
            if cleaned and len(cleaned) > 10:  # Skip very short lines
                bullets.append(cleaned)
        
        # Ensure we have at least something
        if not bullets and raw_response.strip():
            bullets = [raw_response.strip()]
        
        return bullets[:5]  # Max 5 bullets
    
    def _build_sources(
        self, 
        search_results: list[SearchResult], 
        response: str
    ) -> list[Source]:
        """
        Build sources list, only including cited sources.
        
        Args:
            search_results: All search results
            response: The LLM response with citations
            
        Returns:
            List of Source objects that were cited
        """
        # Find all citation numbers in the response
        citations = set(int(m) for m in re.findall(r'\[(\d+)\]', response))
        
        sources = []
        for i, result in enumerate(search_results, 1):
            if i in citations or i <= 3:  # Always include top 3
                sources.append(Source(
                    id=i,
                    title=result.title,
                    url=result.url,
                    snippet=result.snippet[:200] if result.snippet else None
                ))
        
        return sources


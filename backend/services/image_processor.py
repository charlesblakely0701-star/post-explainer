"""Image processing service for extracting context from images."""

import base64
import httpx
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB


class ImageProcessor:
    """Process images for vision model analysis."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
    
    async def download_image(self, url: str) -> Optional[bytes]:
        """
        Download image from URL.
        
        Args:
            url: Image URL
            
        Returns:
            Image bytes or None if failed
        """
        try:
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL is not an image: {content_type}")
                return None
            
            # Check size
            content = response.content
            if len(content) > MAX_IMAGE_SIZE:
                logger.warning(f"Image too large: {len(content)} bytes")
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None
    
    def encode_image_base64(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def get_image_media_type(self, url: str) -> str:
        """
        Get media type from URL extension.
        
        Args:
            url: Image URL
            
        Returns:
            Media type string
        """
        ext = Path(url.split('?')[0]).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        return media_types.get(ext, 'image/jpeg')
    
    async def prepare_image_for_vision(self, url: str) -> Optional[dict]:
        """
        Prepare image for vision model API.
        
        Args:
            url: Image URL
            
        Returns:
            Dict with image data for API, or None if failed
        """
        image_bytes = await self.download_image(url)
        if not image_bytes:
            return None
        
        base64_image = self.encode_image_base64(image_bytes)
        media_type = self.get_image_media_type(url)
        
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{base64_image}",
                "detail": "auto"
            }
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


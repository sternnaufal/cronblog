"""
Image Provider Module
Fetches relevant images for blog articles.
Default: Picsum.photos (free, no API key needed)
Optional: Pexels API (free key from pexels.com)
"""

import logging
import re
import urllib.parse

import requests

from src.config import (
    IMAGE_ENABLED,
    IMAGE_PROVIDER,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    PEXELS_API_KEY,
)

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _extract_keywords(title: str, content: str = "") -> str:
    """
    Extract search keywords from article title and content.
    
    Args:
        title: Article title.
        content: Optional article content for more keywords.
        
    Returns:
        A keyword string suitable for image search.
    """
    # Clean title: remove pipe-separated suffixes, special chars
    keywords = title.split("|")[0].strip()
    # Remove common noise words
    noise = [
        "apa itu", "cara", "tutorial", "belajar", "panduan", 
        "sejarah", "pengertian", " Contoh", "Apa",
    ]
    for word in noise:
        keywords = re.sub(rf"(?i)\b{word}\b", "", keywords)
    keywords = re.sub(r"[^\w\s]", "", keywords).strip()
    # Take first 3 meaningful words
    words = [w for w in keywords.split() if len(w) > 2][:3]
    if not words:
        words = ["teknologi"]
    return " ".join(words)


def _fetch_picsum_url(keyword: str) -> str:
    """
    Get image URL from Picsum.photos (free, no key needed).
    Uses seed param for consistent images per keyword.
    
    Args:
        keyword: Search keyword.
        
    Returns:
        Image URL string.
    """
    seed = urllib.parse.quote(keyword.replace(" ", "-"))
    return f"https://picsum.photos/seed/{seed}/{IMAGE_WIDTH}/{IMAGE_HEIGHT}"


def _fetch_pexels_url(keyword: str) -> str:
    """
    Search for image on Pexels API (free, needs API key).
    
    Args:
        keyword: Search keyword.
        
    Returns:
        Image URL string, or picsum fallback if fails.
    """
    if not PEXELS_API_KEY:
        logger.info("PEXELS_API_KEY not set, falling back to Picsum")
        return _fetch_picsum_url(keyword)

    try:
        url = "https://api.pexels.com/v1/search"
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape",
        }
        headers = {**_HEADERS, "Authorization": PEXELS_API_KEY}

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("photos"):
            photo = data["photos"][0]
            src = photo.get("src", {})
            # Return medium size image
            img_url = src.get("medium") or src.get("large") or src.get("original")
            if img_url:
                logger.info(f"Got image from Pexels: {img_url}")
                return img_url

        logger.warning("No Pexels photos found for keyword: %s", keyword)

    except Exception as e:
        logger.warning(f"Pexels API error: {e}")

    return _fetch_picsum_url(keyword)


def get_image_url(title: str, content: str = "") -> str:
    """
    Get a relevant image URL for the article.
    
    Args:
        title: Article title.
        content: Optional article content.
        
    Returns:
        Image URL string.
    """
    if not IMAGE_ENABLED:
        return ""

    keyword = _extract_keywords(title, content)

    if IMAGE_PROVIDER == "pexels":
        return _fetch_pexels_url(keyword)
    else:
        return _fetch_picsum_url(keyword)


def wrap_image_html(image_url: str, title: str) -> str:
    """
    Wrap image URL in HTML with proper formatting.
    
    Args:
        image_url: The image URL.
        title: Article title for alt text.
        
    Returns:
        HTML string for the image.
    """
    if not image_url:
        return ""

    alt = title.replace('"', "'")[:100]
    
    return (
        f'<div style="text-align: center; margin: 20px 0;">\n'
        f'  <img src="{image_url}" alt="{alt}" '
        f'style="max-width: 100%; height: auto; border-radius: 8px;" />\n'
        f'</div>\n\n'
    )


def inject_image_to_content(content: str, image_html: str) -> str:
    """
    Inject image HTML at the beginning of the article content.
    
    Args:
        content: Original HTML content.
        image_html: Image HTML to inject.
        
    Returns:
        Content with image injected.
    """
    if not image_html:
        return content

    # Insert right before the first <p> tag (image first, then text)
    match = re.search(r"<p[^>]*>", content)
    if match:
        pos = match.start()
        return content[:pos] + "\n" + image_html + content[pos:]
    else:
        return image_html + "\n" + content

"""
Content Generator Module
Generates blog post content using AI APIs.
Provider priority: Custom API (local) > Gemini API > OpenAI API.
Uses the Master Prompt to produce SEO-optimized, human-like articles.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from src.config import (
    CUSTOM_API_BASE_URL,
    CUSTOM_API_KEY,
    CUSTOM_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    IMAGE_ENABLED,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    load_master_prompt,
)
from src.image_provider import get_image_url, inject_image_to_content, wrap_image_html

logger = logging.getLogger(__name__)


class GeneratedArticle:
    """Represents an AI-generated article ready for publishing."""

    def __init__(self, title: str, content: str, labels: List[str]):
        self.title = title.strip()
        self.content = content.strip()
        self.labels = [label.strip() for label in labels if label.strip()]

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "content": self.content,
            "labels": self.labels,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GeneratedArticle":
        return cls(
            title=data.get("title", ""),
            content=data.get("content", ""),
            labels=data.get("labels", []),
        )

    def __repr__(self) -> str:
        return f"GeneratedArticle(title='{self.title}', labels={self.labels})"


def _parse_json_response(raw_text: str) -> Optional[Dict]:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    
    Args:
        raw_text: The raw text response from the LLM.
        
    Returns:
        Parsed dictionary or None if parsing failed.
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    # Try to extract JSON from markdown code block first
    json_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL
    )
    if json_match:
        text = json_match.group(1).strip()

    # Try direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object with curly braces
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    logger.error(f"Failed to parse JSON from LLM response: {text[:200]}...")
    return None


def generate_with_custom_api(
    topic: str, master_prompt: str, backlinks_context: str = ""
) -> Optional[GeneratedArticle]:
    """
    Generate article content using a custom OpenAI-compatible API
    (local/self-hosted: Ollama, vLLM, LocalAI, 9router, etc.).
    
    This is the PRIMARY provider - no API key required for local endpoints.
    
    Args:
        topic: The topic or trend to write about.
        master_prompt: The system instruction / master prompt text.
        backlinks_context: Optional context about existing articles for internal linking.
        
    Returns:
        GeneratedArticle object or None if failed.
    """
    if not CUSTOM_API_BASE_URL:
        logger.warning("CUSTOM_API_BASE_URL not configured, skipping custom API")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=CUSTOM_API_BASE_URL,
            api_key=CUSTOM_API_KEY,
        )

        full_prompt = f"{master_prompt}\n\n{backlinks_context}\n\n{ topic}"

        logger.info(
            f"Generating article with custom API ({CUSTOM_MODEL} @ "
            f"{CUSTOM_API_BASE_URL})..."
        )

        response = client.chat.completions.create(
            model=CUSTOM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda adalah Naufal Rakha Putra, penulis blog Penting Literasi. "
                        "Menulis artikel teknologi dengan gaya santai, engaging, "
                        "dan mudah dipahami. Output dalam format JSON."
                    ),
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.8,
            max_tokens=6144,
        )

        raw_text = response.choices[0].message.content
        if not raw_text:
            logger.error("Custom API returned empty response")
            return None

        parsed = _parse_json_response(raw_text)
        if not parsed:
            logger.error("Custom API response was not valid JSON")
            logger.debug(f"Raw response: {raw_text[:500]}")
            return None

        article = GeneratedArticle.from_dict(parsed)

        if not article.title or not article.content:
            logger.error(
                f"Custom API generated incomplete article: "
                f"title={bool(article.title)}, "
                f"content={bool(article.content)}"
            )
            return None

        logger.info(f"Successfully generated article: '{article.title}'")
        return article

    except ImportError:
        logger.error(
            "openai package not installed. Run: pip install openai"
        )
        return None
    except Exception as e:
        logger.error(f"Custom API error: {e}")
        return None


def generate_with_gemini(
    topic: str, master_prompt: str, backlinks_context: str = ""
) -> Optional[GeneratedArticle]:
    """
    Generate article content using Google Gemini API (google-genai SDK).
    
    Args:
        topic: The topic or trend to write about.
        master_prompt: The system instruction / master prompt text.
        backlinks_context: Optional context about existing articles for internal linking.
        
    Returns:
        GeneratedArticle object or None if failed.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured, skipping Gemini generation")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        full_prompt = f"{master_prompt}\n\n{backlinks_context}\n\n{ topic}"

        logger.info(f"Generating article with Gemini ({GEMINI_MODEL})...")

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                top_p=0.95,
                max_output_tokens=8192,
            ),
        )

        raw_text = response.text
        if not raw_text:
            logger.error("Gemini returned empty response")
            return None

        parsed = _parse_json_response(raw_text)
        if not parsed:
            logger.error("Gemini response was not valid JSON")
            logger.debug(f"Raw response: {raw_text[:500]}")
            return None

        article = GeneratedArticle.from_dict(parsed)

        if not article.title or not article.content:
            logger.error(
                f"Gemini generated incomplete article: title={bool(article.title)}, "
                f"content={bool(article.content)}"
            )
            return None

        logger.info(f"Successfully generated article: '{article.title}'")
        return article

    except ImportError:
        logger.error(
            "google-genai package not installed. Run: pip install google-genai"
        )
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


def generate_with_openai(
    topic: str, master_prompt: str, backlinks_context: str = ""
) -> Optional[GeneratedArticle]:
    """
    Generate article content using OpenAI API (fallback).
    
    Args:
        topic: The topic or trend to write about.
        master_prompt: The system instruction / master prompt text.
        backlinks_context: Optional context about existing articles for internal linking.
        
    Returns:
        GeneratedArticle object or None if failed.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping OpenAI generation")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, timeout=120)

        full_prompt = f"{master_prompt}\n\n{backlinks_context}\n\n{ topic}"

        logger.info(f"Generating article with OpenAI ({OPENAI_MODEL})...")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda adalah Naufal Rakha Putra, penulis blog Penting Literasi. "
                        "Menulis artikel teknologi dengan gaya santai, engaging, "
                        "dan mudah dipahami. Output dalam format JSON."
                    ),
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.8,
            max_tokens=16384,
        )

        raw_text = response.choices[0].message.content
        if not raw_text:
            logger.error("OpenAI returned empty response")
            return None

        parsed = _parse_json_response(raw_text)
        if not parsed:
            logger.error("OpenAI response was not valid JSON")
            return None

        article = GeneratedArticle.from_dict(parsed)

        if not article.title or not article.content:
            logger.error(
                f"OpenAI generated incomplete article: title={bool(article.title)}, "
                f"content={bool(article.content)}"
            )
            return None

        logger.info(f"Successfully generated article: '{article.title}'")
        return article

    except ImportError:
        logger.error(
            "openai package not installed. Run: pip install openai"
        )
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _inject_article_image(article: GeneratedArticle) -> GeneratedArticle:
    """
    Add a relevant image to the article content.
    
    Args:
        article: The generated article.
        
    Returns:
        Article with image injected (or unchanged if disabled).
    """
    if not IMAGE_ENABLED or not article.content:
        return article

    try:
        img_url = get_image_url(article.title, article.content)
        if img_url:
            img_html = wrap_image_html(img_url, article.title)
            article.content = inject_image_to_content(article.content, img_html)
            logger.info(f"Image added to article: {img_url}")
    except Exception as e:
        logger.warning(f"Failed to add image: {e}")

    return article


def generate_article(
    topic: str, backlinks_context: str = ""
) -> Tuple[Optional[GeneratedArticle], str]:
    """
    Generate an article using available AI providers.
    Priority: Custom API (local) > Gemini API > OpenAI API.
    
    Args:
        topic: The topic or trend to write about.
        backlinks_context: Optional context about existing articles for internal linking.
        
    Returns:
        Tuple of (GeneratedArticle or None, provider_name used).
    """
    master_prompt = load_master_prompt()

    # Priority 1: Custom API (local/self-hosted - no rate limits)
    if CUSTOM_API_BASE_URL:
        article = generate_with_custom_api(topic, master_prompt, backlinks_context)
        if article:
            return _inject_article_image(article), "custom"

    # Priority 2: Gemini API (cloud fallback)
    if GEMINI_API_KEY:
        article = generate_with_gemini(topic, master_prompt, backlinks_context)
        if article:
            return _inject_article_image(article), "gemini"

    # Priority 3: OpenAI API (secondary fallback)
    if OPENAI_API_KEY:
        article = generate_with_openai(topic, master_prompt, backlinks_context)
        if article:
            return _inject_article_image(article), "openai"

    logger.error(
        "All AI providers failed. "
        "Make sure your local API is running or check cloud API keys."
    )
    return None, ""

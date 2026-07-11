"""
Content Generator Module
Generates blog post content using Gemini API (primary) or OpenAI API (fallback).
Uses the Master Prompt to produce SEO-optimized, human-like articles.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    load_master_prompt,
)

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


def generate_with_gemini(
    topic: str, master_prompt: str
) -> Optional[GeneratedArticle]:
    """
    Generate article content using Google Gemini API (google-genai SDK).
    
    Args:
        topic: The topic or trend to write about.
        master_prompt: The system instruction / master prompt text.
        
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

        full_prompt = f"{master_prompt}\n\n{ topic}"

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
    topic: str, master_prompt: str
) -> Optional[GeneratedArticle]:
    """
    Generate article content using OpenAI API (fallback).
    
    Args:
        topic: The topic or trend to write about.
        master_prompt: The system instruction / master prompt text.
        
    Returns:
        GeneratedArticle object or None if failed.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping OpenAI generation")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        full_prompt = f"{master_prompt}\n\n{ topic}"

        logger.info(f"Generating article with OpenAI ({OPENAI_MODEL})...")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda adalah seorang Content Writer profesional dan "
                        "pakar SEO. Hasilkan output dalam format JSON."
                    ),
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.8,
            max_tokens=8192,
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


def generate_article(topic: str) -> Tuple[Optional[GeneratedArticle], str]:
    """
    Generate an article using the primary AI provider (Gemini)
    with OpenAI as fallback.
    
    Args:
        topic: The topic or trend to write about.
        
    Returns:
        Tuple of (GeneratedArticle or None, provider_name used).
    """
    master_prompt = load_master_prompt()

    # Try Gemini first (primary)
    if GEMINI_API_KEY:
        article = generate_with_gemini(topic, master_prompt)
        if article:
            return article, "gemini"

    # Fallback to OpenAI
    if OPENAI_API_KEY:
        article = generate_with_openai(topic, master_prompt)
        if article:
            return article, "openai"

    logger.error(
        "All AI providers failed. Check your API keys and internet connection."
    )
    return None, ""

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
    if not raw_text:
        return None

    text = raw_text.strip()

    codeblock = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if codeblock:
        text = codeblock.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    logger.error(f"Failed to parse JSON from LLM response: {text[:200]}...")
    return None


def _extract_openai_text(response) -> Optional[str]:
    try:
        choices = getattr(response, "choices", None)
        if not choices:
            return None
        first = choices[0]
        if not first:
            return None
        message = getattr(first, "message", None)
        if not message:
            return None
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content.strip() or None
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif hasattr(item, "text"):
                    parts.append(getattr(item, "text", ""))
            joined = "".join(parts).strip()
            return joined or None
        return None
    except Exception:
        return None


def _trim_backlinks_context(backlinks_context: str, max_lines: int = 16) -> str:
    if not backlinks_context:
        return ""
    lines = [line for line in backlinks_context.splitlines() if line.strip()]
    return "\n".join(lines[:max_lines])


def _build_full_prompt(master_prompt: str, backlinks_context: str, topic: str) -> str:
    slim_backlinks = _trim_backlinks_context(backlinks_context)
    if slim_backlinks:
        return f"{master_prompt}\n\n{slim_backlinks}\n\n{topic.strip()}"
    return f"{master_prompt}\n\n{topic.strip()}"


def _finalize_article(raw_text: Optional[str], provider_name: str) -> Optional[GeneratedArticle]:
    if not raw_text:
        logger.error(f"{provider_name} returned empty or malformed response")
        return None

    parsed = _parse_json_response(raw_text)
    if not parsed:
        logger.error(f"{provider_name} response was not valid JSON")
        logger.debug(f"Raw response: {raw_text[:500]}")
        return None

    article = GeneratedArticle.from_dict(parsed)
    if not article.title or not article.content:
        logger.error(
            f"{provider_name} generated incomplete article: "
            f"title={bool(article.title)}, content={bool(article.content)}"
        )
        return None
    return article


def _build_messages(full_prompt: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Anda adalah Naufal Rakha Putra, penulis blog Penting Literasi. "
                "Tulis artikel teknologi santai, engaging, mudah dipahami. "
                "Output HARUS JSON valid dengan key: title, content, labels. "
                "Jangan tambahkan teks di luar JSON."
            ),
        },
        {"role": "user", "content": full_prompt},
    ]


def generate_with_custom_api(
    topic: str, master_prompt: str, backlinks_context: str = ""
) -> Optional[GeneratedArticle]:
    if not CUSTOM_API_BASE_URL:
        logger.warning("CUSTOM_API_BASE_URL not configured, skipping custom API")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(base_url=CUSTOM_API_BASE_URL, api_key=CUSTOM_API_KEY)
        full_prompt = _build_full_prompt(master_prompt, backlinks_context, topic)

        logger.info(
            f"Generating article with custom API ({CUSTOM_MODEL} @ "
            f"{CUSTOM_API_BASE_URL})..."
        )

        response = client.chat.completions.create(
            model=CUSTOM_MODEL,
            messages=_build_messages(full_prompt),
            temperature=0.8,
            max_tokens=8192,
        )

        raw_text = _extract_openai_text(response)
        article = _finalize_article(raw_text, "Custom API")
        if article:
            logger.info(f"Successfully generated article: '{article.title}'")
        return article

    except ImportError:
        logger.error("openai package not installed. Run: pip install openai")
        return None
    except Exception as e:
        logger.error(f"Custom API error: {e}")
        return None


def generate_with_gemini(
    topic: str, master_prompt: str, backlinks_context: str = ""
) -> Optional[GeneratedArticle]:
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured, skipping Gemini generation")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        full_prompt = _build_full_prompt(master_prompt, backlinks_context, topic)

        logger.info(f"Generating article with Gemini ({GEMINI_MODEL})...")

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                top_p=0.95,
                max_output_tokens=16384,
            ),
        )

        raw_text = getattr(response, "text", None)
        article = _finalize_article(raw_text, "Gemini")
        if article:
            logger.info(f"Successfully generated article: '{article.title}'")
        return article

    except ImportError:
        logger.error("google-genai package not installed. Run: pip install google-genai")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


def generate_with_openai(
    topic: str, master_prompt: str, backlinks_context: str = ""
) -> Optional[GeneratedArticle]:
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping OpenAI generation")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        full_prompt = _build_full_prompt(master_prompt, backlinks_context, topic)

        logger.info(f"Generating article with OpenAI ({OPENAI_MODEL})...")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=_build_messages(full_prompt),
            temperature=0.8,
            max_tokens=16384,
        )

        raw_text = _extract_openai_text(response)
        article = _finalize_article(raw_text, "OpenAI")
        if article:
            logger.info(f"Successfully generated article: '{article.title}'")
        return article

    except ImportError:
        logger.error("openai package not installed. Run: pip install openai")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _inject_article_image(article: GeneratedArticle) -> GeneratedArticle:
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
    master_prompt = load_master_prompt()

    if CUSTOM_API_BASE_URL:
        article = generate_with_custom_api(topic, master_prompt, backlinks_context)
        if article:
            return _inject_article_image(article), "custom"

    if GEMINI_API_KEY:
        article = generate_with_gemini(topic, master_prompt, backlinks_context)
        if article:
            return _inject_article_image(article), "gemini"

    if OPENAI_API_KEY:
        article = generate_with_openai(topic, master_prompt, backlinks_context)
        if article:
            return _inject_article_image(article), "openai"

    logger.error(
        "All AI providers failed. "
        "Make sure your local API is running or check cloud API keys."
    )
    return None, ""

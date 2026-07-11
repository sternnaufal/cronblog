"""
Trend Fetcher Module
Fetches trending topics from RSS feeds and Google News.
Provides topic suggestions for content generation.
"""

import logging
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import feedparser
import requests
from bs4 import BeautifulSoup

from src.config import RSS_FEEDS

logger = logging.getLogger(__name__)

# Headers to mimic a real browser
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

_HEADERS = {
    "User-Agent": random.choice(_USER_AGENTS),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


class TrendItem:
    """Represents a trending topic item."""

    def __init__(
        self,
        title: str,
        source: str,
        url: str = "",
        summary: str = "",
        published: Optional[datetime] = None,
    ):
        self.title = self._clean_title(title)
        self.source = source
        self.url = url
        self.summary = summary
        self.published = published or datetime.now()

    @staticmethod
    def _clean_title(title: str) -> str:
        """Clean up title text by removing excessive whitespace and source suffixes."""
        title = re.sub(r"\s+", " ", title).strip()
        # Remove common RSS suffix patterns like " - BBC News"
        title = re.sub(r"\s+[-–|]\s+.*$", "", title).strip()
        return title

    def __repr__(self) -> str:
        return f"TrendItem(title='{self.title}', source='{self.source}')"


def fetch_rss_feed(feed_url: str, max_items: int = 10) -> List[TrendItem]:
    """
    Fetch and parse an RSS feed URL.
    
    Args:
        feed_url: The RSS feed URL to fetch.
        max_items: Maximum number of items to return.
        
    Returns:
        List of TrendItem objects.
    """
    items: List[TrendItem] = []

    try:
        logger.info(f"Fetching RSS feed: {feed_url}")
        response = requests.get(
            feed_url,
            headers=_HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        for entry in feed.entries[:max_items]:
            title = entry.get("title", "")
            if not title:
                continue

            summary = entry.get("summary", "")
            # Clean HTML from summary
            if summary:
                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text(separator=" ", strip=True)[:300]

            published = None
            if "published_parsed" in entry and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    published = datetime.now()

            items.append(
                TrendItem(
                    title=title,
                    source=feed_url,
                    url=entry.get("link", ""),
                    summary=summary,
                    published=published,
                )
            )

        logger.info(f"Got {len(items)} items from {feed_url}")

    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch RSS feed {feed_url}: {e}")
    except Exception as e:
        logger.error(f"Error parsing RSS feed {feed_url}: {e}")

    return items


def fetch_google_news_trends(
    query: str = "", max_items: int = 15
) -> List[TrendItem]:
    """
    Fetch trending topics from Google News RSS.
    
    Args:
        query: Optional search query (empty = top headlines).
        max_items: Maximum items to return.
        
    Returns:
        List of TrendItem objects.
    """
    if query:
        feed_url = (
            f"https://news.google.com/rss/search?q={requests.utils.quote(query)}"
            f"&hl=en-US&gl=US&ceid=US:en"
        )
    else:
        feed_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

    return fetch_rss_feed(feed_url, max_items)


def get_trending_topics(max_items: int = 15) -> List[TrendItem]:
    """
    Aggregate trending topics from all configured RSS feeds.
    
    Args:
        max_items: Maximum number of trending items to return.
        
    Returns:
        List of unique TrendItem objects (deduplicated by title).
    """
    all_items: List[TrendItem] = []
    seen_titles: set = set()

    for feed_url in RSS_FEEDS:
        items = fetch_rss_feed(feed_url, max_items=10)
        for item in items:
            # Deduplicate by normalized title
            title_key = item.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_items.append(item)

    # Sort by publish date (most recent first), then limit
    all_items.sort(key=lambda x: x.published, reverse=True)

    logger.info(
        f"Total trending topics collected: {len(all_items)} "
        f"(from {len(RSS_FEEDS)} feeds)"
    )

    return all_items[:max_items]


def format_topics_for_prompt(topics: List[TrendItem], count: int = 5) -> str:
    """
    Format trending topics as a text block for the LLM prompt.
    
    Args:
        topics: List of TrendItem objects.
        count: Number of topics to include.
        
    Returns:
        Formatted string of topics.
    """
    if not topics:
        return "(no trending topics found - write about a general tech topic)"

    # Pick random subset if we have more than requested
    if len(topics) > count:
        selected = random.sample(topics, count)
    else:
        selected = topics

    lines = ["Berikut adalah tren terbaru yang bisa dijadikan topik artikel:\n"]
    for i, topic in enumerate(selected, 1):
        lines.append(f"{i}. {topic.title}")
        if topic.summary:
            # Truncate summary if too long
            summary = topic.summary[:150]
            lines.append(f"   Ringkasan: {summary}...")

    return "\n".join(lines)

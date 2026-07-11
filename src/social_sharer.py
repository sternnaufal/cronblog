"""
Social Share Module
Auto-share published articles to Telegram and/or Twitter/X.
"""

import logging
import urllib.parse
from typing import Optional

import requests

from src.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET,
)

logger = logging.getLogger(__name__)


def _shorten_url(url: str) -> str:
    """Shorten URL using is.gd (free, no API key needed)."""
    try:
        resp = requests.get(
            "https://is.gd/create.php",
            params={"format": "json", "url": url},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if "shorturl" in data:
                return data["shorturl"]
    except Exception as e:
        logger.warning(f"URL shortener failed: {e}")
    return url


def share_telegram(
    title: str,
    url: str,
    summary: str = "",
) -> bool:
    """
    Send article to Telegram channel/group via Bot API.
    
    Args:
        title: Article title.
        url: Article URL.
        summary: Optional short summary (max ~200 chars).
        
    Returns:
        True if successful, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("Telegram not configured, skipping share")
        return False

    try:
        short_url = _shorten_url(url)
        
        # Format message with Markdown
        message = (
            f"📝 *{title}*\n\n"
        )
        if summary:
            message += f"{summary}\n\n"
        message += f"🔗 Baca selengkapnya: {short_url}\n\n"
        message += "#PentingLiterasi #Teknologi #ArtikelBaru"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }

        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("ok"):
            logger.info(f"✅ Shared to Telegram: {title[:50]}")
            return True
        else:
            logger.error(f"Telegram API error: {data}")
            return False

    except Exception as e:
        logger.error(f"Telegram share failed: {e}")
        return False


def share_twitter(
    title: str,
    url: str,
) -> bool:
    """
    Tweet article via Twitter/X API v2.
    Requires Twitter Developer account with OAuth 1.0a.
    
    Args:
        title: Article title.
        url: Article URL.
        
    Returns:
        True if successful, False otherwise.
    """
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        logger.info("Twitter not configured, skipping share")
        return False

    try:
        from requests_oauthlib import OAuth1Session

        short_url = _shorten_url(url)
        
        tweet_text = (
            f"📝 {title}\n\n"
            f"{short_url}\n\n"
            f"#PentingLiterasi #Teknologi #ArtikelBaru"
        )

        # Create OAuth1 session
        oauth = OAuth1Session(
            TWITTER_API_KEY,
            client_secret=TWITTER_API_SECRET,
            resource_owner_key=TWITTER_ACCESS_TOKEN,
            resource_owner_secret=TWITTER_ACCESS_SECRET,
        )

        # Post tweet
        resp = oauth.post(
            "https://api.twitter.com/2/tweets",
            json={"text": tweet_text},
            timeout=15,
        )

        if resp.status_code == 201:
            logger.info(f"✅ Tweeted: {title[:50]}")
            return True
        else:
            logger.error(f"Twitter API error ({resp.status_code}): {resp.text}")
            return False

    except ImportError:
        logger.error("requests-oauthlib not installed. Run: pip install requests-oauthlib")
        return False
    except Exception as e:
        logger.error(f"Twitter share failed: {e}")
        return False


def share_all(
    title: str,
    url: str,
    summary: str = "",
) -> dict:
    """
    Share to all configured platforms.
    
    Args:
        title: Article title.
        url: Article URL.
        summary: Optional short summary for Telegram.
        
    Returns:
        Dict with results for each platform.
    """
    results = {}

    # Telegram
    results["telegram"] = share_telegram(title, url, summary)

    # Twitter/X
    results["twitter"] = share_twitter(title, url)

    return results
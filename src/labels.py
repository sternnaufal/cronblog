"""Ambil daftar label yang sudah dipakai di blog.

Dipakai untuk memberi konteks ke AI agar label baru konsisten dengan
taksonomi blog yang sudah ada.
"""

import logging
from typing import List

import requests

from src.config import BLOGGER_BLOG_ID

logger = logging.getLogger(__name__)

_FEED_URL = (
    "https://www.blogger.com/feeds/{blog_id}/posts/default"
    "?alt=json&max-results={limit}"
)


def fetch_existing_labels(limit: int = 150) -> List[str]:
    """Ambil label unik dari feed publik blog.

    Tidak butuh OAuth, jadi tetap bisa dipakai saat dry-run.
    Mengembalikan list kosong kalau feed gagal diakses.
    """
    if not BLOGGER_BLOG_ID:
        return []

    url = _FEED_URL.format(blog_id=BLOGGER_BLOG_ID, limit=limit)
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        entries = response.json().get("feed", {}).get("entry", [])

        labels = {
            category.get("term", "").strip()
            for entry in entries
            for category in entry.get("category", [])
            if category.get("term", "").strip()
        }
        result = sorted(labels)
        logger.info(f"Loaded {len(result)} existing blog labels")
        return result
    except Exception as e:
        logger.warning(f"Failed to load existing labels: {e}")
        return []

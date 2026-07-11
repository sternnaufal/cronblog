"""
Configuration module for cronblog.
Loads environment variables, settings, and shared utilities.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env file from project root
load_dotenv(PROJECT_ROOT / ".env")


def get_env_str(key: str, default: str = "") -> str:
    """Get a string environment variable."""
    return os.environ.get(key, default)


def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer environment variable."""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_env_list(key: str, default: Optional[List[str]] = None) -> List[str]:
    """Get a comma-separated list environment variable."""
    if default is None:
        default = []
    value = os.environ.get(key, "")
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


# --- AI Provider Settings ---

# Custom OpenAI-compatible API (PRIMARY provider)
# Use any local/self-hosted API (Ollama, vLLM, LocalAI, 9router, etc.)
CUSTOM_API_BASE_URL: str = get_env_str(
    "CUSTOM_API_BASE_URL", "http://localhost:20128/v1"
)
CUSTOM_API_KEY: str = get_env_str("CUSTOM_API_KEY", "not-needed")
CUSTOM_MODEL: str = get_env_str("CUSTOM_MODEL", "combo1")

# Gemini (fallback if custom API fails)
GEMINI_API_KEY: str = get_env_str("GEMINI_API_KEY")
GEMINI_MODEL: str = get_env_str("GEMINI_MODEL", "gemini-2.5-flash")

# OpenAI (secondary fallback)
OPENAI_API_KEY: str = get_env_str("OPENAI_API_KEY")
OPENAI_MODEL: str = get_env_str("OPENAI_MODEL", "gpt-4o-mini")

# --- Blogger Settings ---
BLOGGER_BLOG_ID: str = get_env_str("BLOGGER_BLOG_ID")

# Path to OAuth 2.0 client secrets JSON file
CLIENT_SECRET_PATH: Path = PROJECT_ROOT / "client_secret.json"

# Path to stored OAuth token (auto-generated after first auth)
TOKEN_PATH: Path = PROJECT_ROOT / "token.json"

# Path to service account JSON key file
# Used for server-to-server auth in GitHub Actions
def _find_service_account() -> Path:
    """
    Auto-detect a service account JSON key file.
    Checks: GOOGLE_APPLICATION_CREDENTIALS env var > project root > parent dir.
    """
    # 1. Check environment variable
    env_path = get_env_str("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path:
        return Path(env_path)

    # 2. Check PROJECT_ROOT for *.json files (excluding known files)
    exclude = {"client_secret.json", "token.json", ".env.example"}
    for p in PROJECT_ROOT.glob("*.json"):
        if p.name not in exclude and p.stat().st_size > 100:
            return p

    # 3. Check parent directory (workspace root)
    parent_dir = PROJECT_ROOT.parent
    for p in parent_dir.glob("*.json"):
        if p.name not in exclude and p.stat().st_size > 100:
            return p

    # 4. Default fallback path
    return PROJECT_ROOT / "service-account.json"


SERVICE_ACCOUNT_PATH: Path = _find_service_account()

# --- RSS Feed Sources ---
RSS_FEEDS: List[str] = get_env_list(
    "RSS_FEEDS",
    default=[
        "https://news.google.com/rss",
        "https://feeds.feedburner.com/blogspot/gJZg",
    ],
)

# --- Scheduler Settings ---
# Default: Monday & Thursday at 8:00 AM
CRON_SCHEDULE: str = get_env_str("CRON_SCHEDULE", "0 8 * * 1,4")

# --- Blog Settings ---
MAX_ARTICLES_PER_RUN: int = get_env_int("MAX_ARTICLES_PER_RUN", 1)

# --- Publish Mode ---
# draft     = simpan sebagai draft (default) - review manual dulu
# live      = publish langsung ke blog
# scheduled = publish otomatis setelah PUBLISH_DELAY_HOURS jam
PUBLISH_MODE: str = get_env_str("PUBLISH_MODE", "draft").lower()
PUBLISH_DELAY_HOURS: int = get_env_int("PUBLISH_DELAY_HOURS", 0)

# --- Image Settings ---
# Set IMAGE_ENABLED=true to auto-add images to articles
# Uses Picsum.photos by default (free, no key needed)
# For better results, get a free Pexels API key at https://www.pexels.com/api/
IMAGE_ENABLED: bool = get_env_str("IMAGE_ENABLED", "true").lower() == "true"
IMAGE_PROVIDER: str = get_env_str("IMAGE_PROVIDER", "picsum")  # picsum or pexels
IMAGE_WIDTH: int = get_env_int("IMAGE_WIDTH", 800)
IMAGE_HEIGHT: int = get_env_int("IMAGE_HEIGHT", 400)
PEXELS_API_KEY: str = get_env_str("PEXELS_API_KEY")

# --- Social Share Settings ---
# Telegram (easy, free): buat bot lewat @BotFather, dapatkan token & chat ID
TELEGRAM_BOT_TOKEN: str = get_env_str("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = get_env_str("TELEGRAM_CHAT_ID")

# Twitter/X (butuh Twitter Developer Account + OAuth 1.0a)
TWITTER_API_KEY: str = get_env_str("TWITTER_API_KEY")
TWITTER_API_SECRET: str = get_env_str("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN: str = get_env_str("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET: str = get_env_str("TWITTER_ACCESS_SECRET")

# --- Paths ---
PROMPTS_DIR: Path = PROJECT_ROOT / "prompts"
MASTER_PROMPT_PATH: Path = PROMPTS_DIR / "master_prompt.txt"


def load_master_prompt() -> str:
    """
    Load the master prompt template from prompts/master_prompt.txt.
    
    Returns:
        The master prompt text, or a default prompt if file not found.
    """
    if MASTER_PROMPT_PATH.exists():
        with open(MASTER_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()

    # Fallback default prompt if file doesn't exist
    return """Anda adalah Naufal Rakha Putra, penulis blog "Penting Literasi". Blog fokus teknologi, komputer, OS, programming, hacking, game, sejarah teknologi.

SEO & GAYA PENULISAN:
1. PEMBUKAAN: "Halo, balik lagi di Penting Literasi!" — paragraf pertama max 160 char sebagai meta description.
2. SUASANA: Ngobrol santai, pake "kita", jokes ringan.
3. HEADING: Minimal 3 <h2> per artikel. Keyword utama di minimal 2 heading. <h3> untuk sub-bagian.
4. KEYWORD: Kata kunci utama di judul, H2 pertama, paragraf awal. Bold keyword pake <strong>.
5. TABEL: <table style="border-collapse:collapse;width:100%;margin:15px 0">, <th style="background:#f2f2f2;padding:10px;border:1px solid #ddd;text-align:left">, <td style="padding:8px;border:1px solid #ddd">
6. BAHASA: Indonesian natural + istilah Inggris (booting, coding, dll).
7. KEDALAMAN: 1500-2500 kata, detail teknis + data + studi kasus.
8. LARANGAN: "Di era digital ini...", "Penting untuk diingat...", "Mari kita bahas...", "Kesimpulannya...", "Secara keseluruhan..."
9. PENUTUP: "Punya pengalaman [topik]? Tulis di komentar ya! 😊"
10. LABELS: Satu dari: [Teknologi, Komputer, Sistem Operasi, Windows, Linux, Programming, Python, Java, C++, HTML, JavaScript, Hacking, Teknik Hacking, Jaringan, TKJ, Video Game, Nintendo, Dunia, Sejarah, Informasi]

FORMAT OUTPUT JSON:
{"title": "[Judul dgn keyword, max 60 char sebelum pipe]", "content": "[HTML: <p>meta description</p><p>...</p><h2>...</h2><p>...</p><table>...</table><h2>...</h2><p>...</p>]", "labels": ["[Satu label]"]}

Topik: """


def validate_config() -> List[str]:
    """
    Validate that required configuration is present.
    
    Returns:
        List of missing configuration keys (empty if all valid).
    """
    errors: List[str] = []

    if not CUSTOM_API_BASE_URL and not GEMINI_API_KEY and not OPENAI_API_KEY:
        errors.append(
            "At least one AI provider must be configured in .env:\n"
            "  - CUSTOM_API_BASE_URL (recommended - local/self-hosted API)\n"
            "  - GEMINI_API_KEY (cloud fallback)\n"
            "  - OPENAI_API_KEY (cloud fallback)"
        )

    if not BLOGGER_BLOG_ID:
        errors.append("BLOGGER_BLOG_ID must be set in .env")

    # Check Blogger auth: need at least one auth method available
    has_token = TOKEN_PATH.exists()
    has_client_secret = CLIENT_SECRET_PATH.exists()
    has_service_account = SERVICE_ACCOUNT_PATH.exists() and (
        SERVICE_ACCOUNT_PATH.stat().st_size > 100
    )

    if not has_token and not has_client_secret and not has_service_account:
        errors.append(
            f"No Google authentication method found.\n"
            f"Options:\n"
            f"  1. Add token.json (from OAuth authorization)\n"
            f"  2. Add client_secret.json (OAuth Desktop App credentials)\n"
            f"  3. Add a service account JSON key file in project root\n"
            f"  4. Set GOOGLE_APPLICATION_CREDENTIALS env var"
        )

    return errors

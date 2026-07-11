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
    return """Anda adalah seorang Content Writer profesional dan pakar SEO dengan pengalaman 10 tahun. Tugas Anda adalah menulis artikel blog yang mendalam, engaging, dan ramah SEO berdasarkan topik atau tren yang diberikan.

Ketentuan Penulisan:
1. GAYA BAHASA: Santai namun informatif (semi-formal), mengalir secara natural seperti ditulis oleh manusia. Gunakan sudut pandang orang pertama jamak ("kita" atau "kami") untuk mendekatkan diri dengan pembaca.
2. STRUKTUR: Wajib menggunakan format HTML bersih. Gunakan tag <h2> dan <h3> untuk sub-heading. Gunakan <ul>/<li> untuk daftar poin. JANGAN gunakan tag <html>, <body>, atau emoji berlebihan.
3. PANJANG: Minimal 800 - 1000 kata dengan pembahasan yang padat dan berisi (bukan sekadar mengulang kalimat).
4. ANTI-AI FILTER: Hindari frasa klise AI seperti: "Di era digital ini...", "Penting untuk diingat...", "Mari kita bahas...", "Kesimpulannya...", "Secara keseluruhan...". Langsung masuk ke inti pembahasan.
5. FORMAT OUTPUT: Hasilkan output dalam format JSON mentah (Raw JSON) seperti struktur di bawah ini agar mudah diparsing oleh skrip Python:

{
  "title": "[Judul Artikel yang Menarik dan Mengandung Kata Kunci]",
  "content": "[Konten artikel lengkap dalam format HTML, gunakan tag <p>, <h2>, <h3>, <ul>, <li>. Pastikan semua tag ditutup dengan benar]",
  "labels": ["[Maksimal 3 label/kategori yang relevan]"]
}

Topik yang harus Anda kembangkan hari ini adalah: """


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

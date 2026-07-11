# cronblog - Automated Blogger Publisher

Bot penulis artikel otomatis yang mengambil tren dari RSS feed, menghasilkan konten berkualitas via AI (local/cloud), dan menyimpannya sebagai **Draft** di Blogger untuk kurasi manual.

## Arsitektur

```
[GitHub Actions / Cron Job] (2x seminggu)
         │
         ▼
[Python Script]
         │
         ├──► 1. Ambil Tren (RSS Feed / Google News)
         ├──► 2. Kirim ke AI API (Custom Local API > Gemini > OpenAI)
         └──► 3. Kirim ke Blogger API v3 (Status: DRAFT)
```

## Fitur

- **Trend Fetching**: Mengambil topik tren dari RSS feed (Google News, dll.)
- **AI Content Generation**: Custom local API (primary) + Gemini/OpenAI (fallback)
- **Draft System**: Semua artikel disimpan sebagai **DRAFT** di Blogger untuk kurasi manual
- **Anti-AI Filter**: Master prompt dirancang untuk menghasilkan teks alami tanpa jejak AI
- **Scheduled**: Berjalan otomatis 2x seminggu via GitHub Actions
- **Triple Provider**: Custom API > Gemini API > OpenAI API (failover cascade)

## Struktur Folder

```
cronblog/
├── .github/workflows/
│   └── publish.yml              # GitHub Actions workflow
├── prompts/
│   └── master_prompt.txt        # System instruction untuk AI
├── src/
│   ├── __init__.py
│   ├── main.py                  # Entry point CLI
│   ├── config.py                # Konfigurasi & env vars
│   ├── trend_fetcher.py         # RSS feed scraper
│   ├── content_generator.py     # Custom API / Gemini / OpenAI
│   └── blogger_publisher.py     # Blogger API v3 client
├── .env.example                 # Template environment variables
├── requirements.txt             # Python dependencies
└── README.md
```

## Setup

### 1. Prasyarat

- Python 3.10+
- Local AI API (Ollama, vLLM, 9router, dll.) atau cloud API key (Gemini/OpenAI)
- Google Cloud Project dengan Blogger API diaktifkan

### 2. Instalasi

```bash
# Clone repo dan masuk ke folder cronblog
cd cronblog

# Buat virtual environment
python -m venv venv
.\venv\Scripts\activate    # Windows
# source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Konfigurasi

```bash
# Copy .env.example ke .env
copy .env.example .env

# Edit .env - cukup set:
#   CUSTOM_API_BASE_URL=http://localhost:20128/v1
#   BLOGGER_BLOG_ID=your_blog_id
```

### 4. Google OAuth Setup

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau pilih project yang sudah ada
3. Aktifkan **Blogger API v3** di Library
4. Buat **OAuth 2.0 Client ID** (Desktop application)
5. Download JSON → rename ke `client_secret.json`
6. Letakkan di root folder `cronblog/`
7. Jalankan sekali: `python -m src.main` untuk proses OAuth (buka browser)

### 5. GitHub Secrets Setup

> **Catatan**: GitHub Actions tidak bisa akses `localhost`. Pastikan setidaknya
> Gemini atau OpenAI API key sebagai fallback untuk CI/CD.

| Secret | Deskripsi |
|--------|-----------|
| `CUSTOM_API_BASE_URL` | Local API URL (localhost - skip di CI) |
| `GEMINI_API_KEY` | Google Gemini API Key (fallback) |
| `OPENAI_API_KEY` | OpenAI API Key (fallback) |
| `BLOGGER_BLOG_ID` | Blogger Blog ID |
| `BLOGGER_CLIENT_SECRET_JSON` | client_secret.json (base64) |
| `BLOGGER_TOKEN_JSON` | token.json (base64 - dari hasil OAuth) |

## Provider Priority

Sistem menggunakan cascade failover:

1. **Custom API** (local) — tidak ada rate limit, gratis
2. **Gemini API** — cloud fallback jika local down
3. **OpenAI API** — secondary fallback

## Penggunaan

### CLI

```bash
# Validasi konfigurasi
python -m src.main --validate

# Generate + publish (full pipeline)
python -m src.main

# Dry-run (generate saja, tanpa publish)
python -m src.main --dry-run

# Custom topic
python -m src.main --topic "Perkembangan AI di Indonesia 2026"

# Verbose logging
python -m src.main --verbose
```

### GitHub Actions

Workflow otomatis berjalan setiap **Senin & Kamis jam 08:00 UTC**.

Bisa juga di-trigger manual dari tab **Actions** > **cronblog** > **Run workflow**.

## Master Prompt

File `prompts/master_prompt.txt` berisi system instruction untuk AI. Prompt ini didesain untuk:

- Gaya bahasa santai-informatif (semi-formal)
- Output JSON siap pakai
- Anti-AI filter (hindari frasa klise)
- Minimal 800-1000 kata
- Format HTML bersih

## Tech Stack

- **Python 3.10+**
- **OpenAI SDK** (custom API + OpenAI fallback)
- **google-genai** (Gemini API SDK)
- **google-api-python-client** (Blogger API v3)
- **feedparser** (RSS parsing)
- **GitHub Actions** (Scheduling)

## Notes

- Semua artikel dibuat sebagai **DRAFT** - tidak otomatis terpublish
- Review dan publish manual di [Blogger Dashboard](https://www.blogger.com/)
- Pastikan token OAuth direfresh secara berkala
- Local API (9router/Ollama) harus berjalan saat eksekusi lokal

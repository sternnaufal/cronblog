# cronblog - Automated Blogger Publisher

Bot penulis artikel otomatis yang mengambil tren dari RSS feed, menghasilkan konten berkualitas via AI (Gemini/OpenAI), dan menyimpannya sebagai **Draft** di Blogger untuk kurasi manual.

## Arsitektur

```
[GitHub Actions / Cron Job] (2x seminggu)
         │
         ▼
[Python Script]
         │
         ├──► 1. Ambil Tren (RSS Feed / Google News)
         ├──► 2. Kirim ke Gemini/OpenAI API (Master Prompt)
         └──► 3. Kirim ke Blogger API v3 (Status: DRAFT)
```

## Fitur

- **Trend Fetching**: Mengambil topik tren dari RSS feed (Google News, dll.)
- **AI Content Generation**: Menghasilkan artikel SEO-friendly via Gemini API atau OpenAI API
- **Draft System**: Semua artikel disimpan sebagai **DRAFT** di Blogger untuk kurasi manual
- **Anti-AI Filter**: Master prompt dirancang untuk menghasilkan teks alami tanpa jejak AI
- **Scheduled**: Berjalan otomatis 2x seminggu via GitHub Actions
- **Dual Provider**: Gemini sebagai primary, OpenAI sebagai fallback

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
│   ├── content_generator.py     # Gemini/OpenAI integration
│   └── blogger_publisher.py     # Blogger API v3 client
├── .env.example                 # Template environment variables
├── requirements.txt             # Python dependencies
└── README.md
```

## Setup

### 1. Prasyarat

- Python 3.10+
- Google Cloud Project dengan Blogger API diaktifkan
- Gemini API Key atau OpenAI API Key

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

# Edit .env dengan kredensial kamu
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

| Secret | Deskripsi |
|--------|-----------|
| `GEMINI_API_KEY` | Google Gemini API Key |
| `OPENAI_API_KEY` | OpenAI API Key (fallback) |
| `BLOGGER_BLOG_ID` | Blogger Blog ID |
| `BLOGGER_CLIENT_SECRET_JSON` | client_secret.json (base64) |
| `BLOGGER_TOKEN_JSON` | token.json (base64 - dari hasil OAuth) |

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
- **google-genai** (Gemini API SDK baru)
- **google-api-python-client** (Blogger API v3)
- **feedparser** (RSS parsing)
- **GitHub Actions** (Scheduling)

## Notes

- Semua artikel dibuat sebagai **DRAFT** - tidak otomatis terpublish
- Review dan publish manual di [Blogger Dashboard](https://www.blogger.com/)
- Pastikan token OAuth direfresh secara berkala

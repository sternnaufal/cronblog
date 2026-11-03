# cronblog - Automated Blogger Publisher

Bot penulis artikel otomatis yang mengambil topik dari **queue manual** (atau tren RSS sebagai fallback), menghasilkan konten via AI, lalu menyimpannya sebagai **Draft** atau langsung **Live** di Blogger.

## Arsitektur

```
[Cron server / GitHub Actions]
         │
         ▼
[Python Script]
         │
         ├──► 1. Ambil Topik (queue manual → fallback RSS)
         ├──► 2. Kirim ke AI API (Custom API > Gemini > OpenAI)
         ├──► 3. Pilih 3-5 label (pakai taksonomi blog)
         └──► 4. Kirim ke Blogger API v3 (DRAFT / LIVE)
```

## Fitur

- **Queue Topik Manual**: tentukan topik di `blog_title_queue.txt`
- **Trend Fetching**: fallback otomatis ke RSS teknologi/internet
- **AI Content Generation**: Custom API (primary) + Gemini/OpenAI (fallback)
- **Streaming**: aman untuk artikel panjang di gateway dengan timeout
- **Label Dinamis**: 3-5 label per artikel, label baru dibuat bila perlu
- **Draft / Live Mode**: pilih kurasi manual atau langsung tayang
- **Anti-AI Filter**: Master prompt dirancang untuk teks natural tanpa frasa klise
- **Scheduled**: cron harian (default 12.00 WIB)
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
│   ├── topic_queue.py           # Queue topik manual
│   ├── labels.py                # Taksonomi label blog
│   ├── content_generator.py     # Custom API / Gemini / OpenAI
│   └── blogger_publisher.py     # Blogger API v3 client
├── auth.py                      # OAuth di laptop (ada browser)
├── auth_server.py               # OAuth headless via SSH tunnel
├── run.sh                       # Wrapper cron + flock
├── blog_title_queue.txt         # Daftar topik manual
├── VERSION
├── CHANGELOG.md
├── DEVLOG.md
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
7. Generate token OAuth:
   - Di komputer dengan browser: `python auth.py`
   - Di server headless: `python auth_server.py`, lalu dari laptop buat
     SSH tunnel `ssh -L 8080:localhost:8080 user@server` dan buka URL yang
     tercetak.
8. Set OAuth consent screen ke **In production** agar refresh token tidak
   kedaluwarsa dalam 7 hari (status Testing).

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

# Cek versi
python -m src.main --version
```

### Queue Topik Manual

Isi `blog_title_queue.txt`, satu topik per baris:

```text
Cara kerja DNS buat pemula
Apa itu zero-day exploit?
Sejarah Linux di server
```

- Bot mengambil topik dari atas.
- Baris kosong dan baris berawalan `#` diabaikan.
- Topik dihapus hanya setelah publish berhasil.
- Riwayat topik ada di `blog_title_queue.done.txt`.
- Kalau queue kosong, bot fallback ke RSS.

### Label Dinamis

Bot mengambil daftar label yang sudah ada dari feed blog, lalu meminta AI
memilih 3-5 label. Label pertama wajib spesifik ke topik utama; label baru
dibuat otomatis kalau topiknya belum pernah dibahas.

### Scheduling

#### Cron di server

```cron
0 12 * * * /path/ke/cronblog/run.sh >> /path/ke/cronblog/logs/cron.log 2>&1
```

`run.sh` memakai `flock` supaya dua run tidak berjalan bersamaan.

#### GitHub Actions

Workflow `publish.yml` masih tersedia dan bisa dijalankan manual dari tab
**Actions**. Jadwal default di workflow adalah Senin & Kamis 08:00 UTC.

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

- Mode default `PUBLISH_MODE=draft`. Set `live` kalau ingin langsung tayang.
- Draft bisa direview di [Blogger Dashboard](https://www.blogger.com/).
- `token.json` disimpan di server dengan permission `600`; jangan di-commit.
- Pantau hasil run di `logs/cron.log`.
- Local API (9router/Ollama) harus berjalan kalau memakai provider lokal.
- Blogger API v3 belum mendukung pengisian "Search Description" per artikel.
  Meta description otomatis bisa dilakukan lewat edit tema (`data:post.snippet`).

## Versi

Versi saat ini: **1.1.0**. Lihat `VERSION`, `CHANGELOG.md`, dan `DEVLOG.md`.


---

Dibuat oleh [Naufal Rakha Putra](https://www.naufalrakha.my.id) — lihat proyek lainnya di [naufalrakha.my.id](https://www.naufalrakha.my.id)

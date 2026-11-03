# Changelog

Semua perubahan penting pada proyek ini didokumentasikan di file ini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/),
dan versi mengikuti [Semantic Versioning](https://semver.org/lang/id/).

## [1.1.0] - 2026-11-03

Rilis fitur: queue topik manual, label dinamis, streaming, dan otomasi server.

### Added

- **Queue topik manual** (`blog_title_queue.txt` + `src/topic_queue.py`).
  Topik diambil berurutan, hanya dihapus setelah publish berhasil, dan
  riwayatnya dicatat di `blog_title_queue.done.txt`. Kalau queue kosong,
  bot fallback ke RSS.
- **Label dinamis** (`src/labels.py`). Bot membaca label yang sudah ada dari
  feed blog, lalu meminta AI memilih 3-5 label. Label baru dibuat otomatis
  kalau topiknya belum pernah dibahas.
- **Helper OAuth**:
  - `auth.py` untuk generate `token.json` di komputer yang ada browser.
  - `auth_server.py` untuk server headless lewat SSH tunnel.
- **Wrapper cron** `run.sh` dengan `flock` untuk mencegah dua run bersamaan.
- **Aturan niche** di master prompt: fokus teknologi, internet, komputer,
  programming, sistem operasi, keamanan siber, jaringan, dan video game.
- **`--dry-run` tanpa kredensial Blogger**, berguna untuk menguji pipeline
  sebelum OAuth selesai.

### Changed

- Custom API sekarang memakai **streaming**, menghindari timeout gateway
  sekitar 90 detik pada artikel panjang.
- Sumber RSS default diganti ke feed teknologi/internet: Google News Tekno ID,
  Google News OS/Coding ID, The Hacker News, The Register, dan DailySocial.
- Instruksi label diubah dari satu label statis menjadi 3-5 label dinamis
  dengan konteks taksonomi blog.
- Dokumentasi setup OAuth diperbarui untuk status **In production** agar
  refresh token tidak kedaluwarsa dalam 7 hari.

### Fixed

- Request non-streaming yang gagal `502 Bad Gateway` saat generate artikel
  panjang.
- `validate_config()` tidak lagi mewajibkan autentikasi Blogger pada mode
  `--dry-run`.
- Label yang sebelumnya selalu jatuh ke satu kategori umum sekarang mengikuti
  topik artikel.

### Notes

- Mode publish default tetap `draft`. Ubah `PUBLISH_MODE=live` di `.env`
  kalau ingin langsung tayang.
- `.env`, `token.json`, `client_secret.json`, dan state runtime tidak pernah
  di-commit.

## [1.0.0] - 2026-11-03

### Baseline

Versi awal sebelum pengembangan ini: pipeline dari RSS, satu label statis,
mode draft, scheduling lewat GitHub Actions, dan dukungan provider
Custom API / Gemini / OpenAI.


"""Helper OAuth Blogger.

Jalankan sekali di komputer yang punya browser:

    python auth.py

File client_secret.json harus ada di folder yang sama. Setelah browser
selesai authorize, token.json akan dibuat otomatis. Copy token.json ke
server ini di /home/pityuwa/cronblog/token.json.
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

from src.blogger_publisher import authenticate  # noqa: E402

if __name__ == "__main__":
    creds = authenticate()
    if creds:
        print("\nOAuth berhasil. token.json sudah dibuat.")
    else:
        print("\nOAuth gagal. Pastikan client_secret.json ada dan Blogger API aktif.")

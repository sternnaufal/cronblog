"""OAuth Blogger untuk server headless (butuh SSH tunnel).

Jalankan di server, lalu dari laptop:

    ssh -L 8080:localhost:8080 pityuwa@<ip-server>

Buka URL authorization yang tercetak, login, dan token.json akan
tersimpan otomatis di folder ini.
"""

import logging

from google_auth_oauthlib.flow import InstalledAppFlow

from src.blogger_publisher import SCOPES
from src.config import CLIENT_SECRET_PATH, TOKEN_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH), SCOPES
    )
    creds = flow.run_local_server(
        host="localhost",
        port=8080,
        open_browser=False,
        authorization_prompt_message=(
            "\nBuka URL ini di browser laptop (setelah SSH tunnel aktif):\n\n{url}\n"
        ),
        success_message="Otorisasi berhasil. Kamu boleh menutup tab ini.",
    )
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"token.json tersimpan di {TOKEN_PATH}")

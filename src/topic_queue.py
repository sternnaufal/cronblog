"""Queue topik manual untuk cronblog.

Format `blog_title_queue.txt`: satu topik per baris.
Baris kosong dan baris yang diawali `#` diabaikan.

Topik yang berhasil diproses dipindahkan ke `blog_title_queue.done.txt`
beserta timestamp, sehingga tidak diulang di run berikutnya.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from src.config import PROJECT_ROOT

QUEUE_PATH: Path = PROJECT_ROOT / "blog_title_queue.txt"
DONE_PATH: Path = PROJECT_ROOT / "blog_title_queue.done.txt"

logger = logging.getLogger(__name__)


def _read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _is_topic(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def peek_topics(limit: int = 1) -> List[str]:
    """Ambil topik teratas tanpa menghapusnya dari queue."""
    topics: List[str] = []
    for line in _read_lines(QUEUE_PATH):
        if _is_topic(line):
            topics.append(line.strip())
            if len(topics) >= limit:
                break
    return topics


def consume_topic(topic: str) -> None:
    """Hapus satu kemunculan topik dari queue dan catat sebagai selesai."""
    lines = _read_lines(QUEUE_PATH)
    remaining: List[str] = []
    removed = False

    for line in lines:
        if not removed and line.strip() == topic.strip():
            removed = True
            continue
        remaining.append(line)

    if not removed:
        logger.warning(f"Topic not found in queue, nothing removed: {topic}")
        return

    content = "\n".join(remaining).strip()
    QUEUE_PATH.write_text(content + ("\n" if content else ""), encoding="utf-8")

    with DONE_PATH.open("a", encoding="utf-8") as done_file:
        stamp = datetime.now().isoformat(timespec="seconds")
        done_file.write(f"{stamp}\t{topic}\n")

    logger.info(f"Topic removed from queue: {topic}")


def queue_size() -> int:
    """Jumlah topik yang masih menunggu di queue."""
    return len(peek_topics(limit=10_000))

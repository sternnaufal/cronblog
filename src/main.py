"""
Main entry point for cronblog - Automated Blogger Publisher.

Flow:
1. Validate configuration
2. Fetch trending topics from RSS feeds
3. Select best topic(s) for article generation
4. Generate article content using AI (Custom API > Gemini > OpenAI)
5. Publish to Blogger (DRAFT / LIVE / SCHEDULED)

Usage:
    python -m src.main                    # Generate and publish
    python -m src.main --dry-run          # Generate only (no publish)
    python -m src.main --topic "..."      # Custom topic (skip trend fetch)
    python -m src.main --validate         # Validate config only
"""

import argparse
import logging
import sys
from typing import List, Optional

from src.blogger_publisher import (
    authenticate,
    format_posts_for_backlinks,
    list_recent_posts,
    publish_post,
)
from src.config import (
    MAX_ARTICLES_PER_RUN,
    PUBLISH_DELAY_HOURS,
    PUBLISH_MODE,
    validate_config,
)
from src.content_generator import generate_article
from src.trend_fetcher import (
    TrendItem,
    format_topics_for_prompt,
    get_trending_topics,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cronblog")


def setup_argparse() -> argparse.ArgumentParser:
    """Configure command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="cronblog - Automated Blogger Publisher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                    # Full pipeline (default)
  python -m src.main -i                 # Interactive mode (pilih2 sendiri)
  python -m src.main --dry-run          # Generate article without publishing
  python -m src.main --topic "AI trends"  # Custom topic
  python -m src.main --validate         # Check configuration only
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate article but do NOT publish to Blogger",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Custom topic (skip trend fetching)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode: pilih topic & publish mode manual",
    )

    return parser


def run_interactive() -> int:
    """
    Interactive CLI wizard - user chooses topic, mode, etc.
    
    Returns:
        Exit code.
    """
    from src.config import (
        IMAGE_ENABLED as _img_enabled,
        PUBLISH_MODE as _publish_mode,
    )
    from src.trend_fetcher import get_trending_topics, format_topics_for_prompt

    print()
    print("=" * 55)
    print("  🚀  cronblog - Interactive Mode")
    print("=" * 55)
    print()

    # --- Step 1: Topic ---
    print("📝  PILIH TOPIK:")
    print("  1. Ambil dari tren RSS")
    print("  2. Tulis manual")
    print()
    topic_choice = input("  Pilih (1/2): ").strip()

    topic = ""
    if topic_choice == "1":
        print("\n  Mengambil tren terkini...")
        trends = get_trending_topics(max_items=10)
        if trends:
            print(f"\n  Topik tren tersedia:")
            for i, t in enumerate(trends[:8], 1):
                print(f"    {i}. {t.title[:70]}")
            print()
            idx = input("  Pilih nomor (enter = acak): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(trends):
                topic = trends[int(idx) - 1].title
            else:
                import random
                topic = random.choice(trends).title
                print(f"  (acak) {topic[:70]}")
        else:
            print("  (tidak ada tren, pake topik default)")
            topic = "Perkembangan Teknologi AI 2026"
    else:
        topic = input("\n  Masukkan topik: ").strip()
        if not topic:
            topic = input("  (topik kosong, ulangi): ").strip()

    print()

    # --- Step 2: Publish Mode ---
    print("📤  PILIH MODE PUBLISH:")
    print("  1. Draft (simpan dulu, review manual)")
    print("  2. Live (publish langsung)")
    print("  3. Scheduled (jadwal, misal 6 jam lagi)")
    print()
    mode_choice = input("  Pilih (1/2/3): ").strip()

    publish_mode = "draft"
    delay = 0
    if mode_choice == "2":
        publish_mode = "live"
    elif mode_choice == "3":
        publish_mode = "scheduled"
        delay_input = input("  Delay berapa jam? (enter = 6): ").strip()
        delay = int(delay_input) if delay_input.isdigit() else 6

    # --- Step 3: Images ---
    print()
    img_choice = input("  Tambah gambar? (Y/n): ").strip().lower()
    image_enabled = img_choice != "n"

    # --- Preview ---
    print()
    print("-" * 55)
    print("  RINGKASAN:")
    print(f"    Topik   : {topic[:60]}")
    print(f"    Mode    : {publish_mode.upper()}"
          + (f" (+{delay}h)" if publish_mode == "scheduled" else ""))
    print(f"    Gambar  : {'Ya' if image_enabled else 'Tidak'}")
    print("-" * 55)
    print()

    confirm = input("  Lanjutkan? (Y/n): ").strip().lower()
    if confirm == "n":
        print("  Dibatalkan.")
        return 0

    # --- Step 4: Override env vars & Run ---
    import os
    os.environ["PUBLISH_MODE"] = publish_mode
    if publish_mode == "scheduled":
        os.environ["PUBLISH_DELAY_HOURS"] = str(delay)
    os.environ["IMAGE_ENABLED"] = "true" if image_enabled else "false"

    print()
    return run_pipeline(dry_run=False, custom_topic=topic, num_articles=1)


def run_pipeline(
    dry_run: bool = False,
    custom_topic: Optional[str] = None,
    num_articles: int = 1,
) -> int:
    """
    Run the full content generation and publishing pipeline.
    
    Args:
        dry_run: If True, skip publishing to Blogger.
        custom_topic: If provided, skip trend fetching.
        num_articles: Number of articles to generate.
        
    Returns:
        Exit code (0 = success).
    """
    # Step 1: Determine topic(s) to write about
    if custom_topic:
        logger.info(f"Using custom topic: {custom_topic}")
        topics = [custom_topic]
    else:
        logger.info("Fetching trending topics from RSS feeds...")
        trends: List[TrendItem] = get_trending_topics(max_items=15)

        if not trends:
            logger.warning(
                "No trending topics found. Using general tech topic."
            )
            topics = [
                "Perkembangan teknologi AI dan dampaknya pada kehidupan sehari-hari"
            ]
        else:
            topic_text = format_topics_for_prompt(trends, count=5)
            logger.info(f"Trending topics:\n{topic_text}")
            topics = [topic_text]

    # Step 2: Authenticate with Blogger (early, to fail fast)
    if not dry_run:
        logger.info("Authenticating with Blogger API...")
        creds = authenticate()
        if not creds:
            logger.error(
                "Failed to authenticate with Blogger. "
                "Run --validate to check configuration."
            )
            return 1
    else:
        creds = None
        logger.info("Dry-run mode: Skipping Blogger authentication")

    # Step 2.5: Fetch recent posts for internal backlink context
    backlinks_context = ""
    if creds:
        logger.info("Fetching recent posts for backlink references...")
        recent_posts = list_recent_posts(max_results=8, creds=creds)
        backlinks_context = format_posts_for_backlinks(recent_posts)
        logger.info(f"Backlink context: {len(recent_posts)} article(s) available")

    # Step 3: Generate and publish articles
    success_count = 0
    for i in range(min(num_articles, len(topics))):
        topic = topics[i] if i < len(topics) else topics[-1]

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing article {i+1}/{num_articles}")
        logger.info(f"{'='*60}")

        # Generate article
        logger.info("Generating article content with AI...")
        article, provider = generate_article(topic, backlinks_context)

        if not article:
            logger.error(
                f"Failed to generate article #{i+1}. "
                f"Check your API keys and try again."
            )
            continue

        logger.info(f"✅ Article generated using {provider}:")
        logger.info(f"   Title: {article.title}")
        logger.info(f"   Labels: {article.labels}")
        logger.info(f"   Content length: {len(article.content)} chars")

        # Publish to Blogger
        if not dry_run:
            logger.info(f"Publishing to Blogger (mode: {PUBLISH_MODE})...")
            result = publish_post(
                title=article.title,
                content=article.content,
                labels=article.labels,
                creds=creds,
            )

            if result:
                success_count += 1
                status = result.get("status", "unknown")
                post_url = result.get("url", "")
                logger.info(
                    f"✅ Article #{i+1} published! "
                    f"Status: {status} | "
                    f"URL: {post_url}"
                )

                # Auto social share (only for LIVE mode - article sudah tayang)
                if status.lower() == "live":
                    try:
                        from src.config import (
                            TELEGRAM_BOT_TOKEN,
                            TELEGRAM_CHAT_ID,
                        )
                        has_telegram = bool(
                            TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
                        )
                        from src.config import TWITTER_API_KEY
                        has_twitter = bool(TWITTER_API_KEY)

                        if has_telegram or has_twitter:
                            from src.social_sharer import share_all
                            logger.info("  Sharing to social media...")
                            results = share_all(
                                title=article.title,
                                url=post_url,
                            )
                            for platform, ok in results.items():
                                if ok:
                                    logger.info(f"    ✅ {platform}")
                                else:
                                    logger.info(f"    - {platform} (skip)")
                    except Exception as e:
                        logger.warning(f"Social share error: {e}")
            else:
                logger.error(f"❌ Failed to publish article #{i+1}")
        else:
            success_count += 1
            logger.info(
                f"✅ Article #{i+1} generated (dry-run, not published)"
            )

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Pipeline complete: {success_count}/{num_articles} successful")
    logger.info(f"{'='*60}")

    if success_count > 0 and not dry_run:
        if PUBLISH_MODE == "draft":
            logger.info(
                "\n📝 Drafts saved to Blogger. "
                "Review and publish manually at: "
                "https://www.blogger.com/"
            )
        elif PUBLISH_MODE == "scheduled":
            logger.info(
                f"\n⏰ Articles scheduled! "
                f"Will publish in {PUBLISH_DELAY_HOURS} hours."
            )
        else:
            logger.info(
                "\n🚀 Articles published live! "
                f"Check at: https://blog.naufalrakha.my.id/"
            )

    return 0 if success_count > 0 else 1


def main() -> int:
    """
    CLI entry point for cronblog.
    
    Returns:
        Exit code.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("🚀 cronblog - Automated Blogger Publisher")
    logger.info("=" * 50)

    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        logger.error("Configuration errors found:")
        for error in config_errors:
            logger.error(f"  • {error}")
        logger.error(
            "\nFix the issues above and try again. "
            "Copy .env.example to .env and fill in your credentials."
        )
        return 1

    if args.validate:
        logger.info("✅ Configuration is valid!")
        return 0

    if args.interactive:
        return run_interactive()

    logger.info(f"Max articles per run: {MAX_ARTICLES_PER_RUN}")
    logger.info(f"Dry-run mode: {'ON' if args.dry_run else 'OFF'}")

    # Run pipeline
    return run_pipeline(
        dry_run=args.dry_run,
        custom_topic=args.topic,
        num_articles=MAX_ARTICLES_PER_RUN,
    )


if __name__ == "__main__":
    sys.exit(main())

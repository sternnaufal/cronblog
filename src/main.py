"""
Main entry point for cronblog - Automated Blogger Publisher.

Flow:
1. Validate configuration
2. Fetch trending topics from RSS feeds
3. Select best topic(s) for article generation
4. Generate article content using Gemini/OpenAI API
5. Publish as DRAFT to Blogger

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

from src.blogger_publisher import authenticate, publish_draft
from src.config import (
    MAX_ARTICLES_PER_RUN,
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
  python -m src.main                    # Full pipeline
  python -m src.main --dry-run          # Generate article without publishing
  python -m src.main --topic "AI trends 2026"  # Custom topic
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

    return parser


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

    # Step 3: Generate and publish articles
    success_count = 0
    for i in range(min(num_articles, len(topics))):
        topic = topics[i] if i < len(topics) else topics[-1]

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing article {i+1}/{num_articles}")
        logger.info(f"{'='*60}")

        # Generate article
        logger.info("Generating article content with AI...")
        article, provider = generate_article(topic)

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

        # Publish as draft
        if not dry_run:
            logger.info("Publishing as draft to Blogger...")
            result = publish_draft(
                title=article.title,
                content=article.content,
                labels=article.labels,
                creds=creds,
            )

            if result:
                success_count += 1
                logger.info(
                    f"✅ Article #{i+1} saved as draft! "
                    f"URL: {result.get('url', 'unknown')}"
                )
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
        logger.info(
            "\n📝 Drafts saved to Blogger. "
            "Review and publish manually at: "
            "https://www.blogger.com/"
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

"""
Blogger Publisher Module
Handles authentication and publishing to Blogger API v3.
Creates posts as DRAFT for manual review before publishing.
"""

import json
import logging
import os
from typing import Dict, List, Optional

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as SACredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import (
    BLOGGER_BLOG_ID,
    CLIENT_SECRET_PATH,
    PUBLISH_DELAY_HOURS,
    PUBLISH_MODE,
    SERVICE_ACCOUNT_PATH,
    TOKEN_PATH,
)

logger = logging.getLogger(__name__)

# Blogger API v3 scope (read/write)
SCOPES = ["https://www.googleapis.com/auth/blogger"]


def _authenticate_via_token() -> Optional[Credentials]:
    """Try to load existing OAuth token from token.json."""
    if not TOKEN_PATH.exists():
        return None

    try:
        with open(TOKEN_PATH, "r") as token_file:
            token_data = json.load(token_file)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        logger.info("Loaded existing OAuth token from token.json")
        return creds
    except (json.JSONDecodeError, ValueError, Exception) as e:
        logger.warning(f"Failed to load token.json: {e}")
        return None


def _authenticate_via_service_account() -> Optional[SACredentials]:
    """Try to authenticate using a Google service account JSON key file."""
    if not SERVICE_ACCOUNT_PATH.exists():
        return None

    try:
        creds = SACredentials.from_service_account_file(
            str(SERVICE_ACCOUNT_PATH),
            scopes=SCOPES,
        )
        logger.info(
            "Authenticated using service account: "
            f"{SERVICE_ACCOUNT_PATH.name}"
        )
        return creds
    except Exception as e:
        logger.warning(f"Failed to authenticate via service account: {e}")
        return None


def _authenticate_via_oauth_flow() -> Optional[Credentials]:
    """
    Start interactive OAuth 2.0 flow using client_secret.json.
    Requires a browser (interactive mode).
    """
    if not CLIENT_SECRET_PATH.exists():
        logger.error(
            f"OAuth client secrets file not found at: {CLIENT_SECRET_PATH}\n"
            f"Download from Google Cloud Console > APIs & Services > Credentials.\n"
            f"Create an OAuth 2.0 Client ID (Desktop application) and save as "
            f"client_secret.json in the project root."
        )
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_PATH, SCOPES
        )
        creds = flow.run_local_server(
            port=0,
            open_browser=True,
        )
        logger.info("Completed OAuth 2.0 authorization flow")

        # Save token for next run
        try:
            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Saved OAuth token to {TOKEN_PATH}")
        except Exception as e:
            logger.warning(f"Failed to save token.json: {e}")

        return creds
    except Exception as e:
        logger.error(f"OAuth authorization failed: {e}")
        return None


def authenticate() -> Optional[Credentials]:
    """
    Authenticate with Google Blogger API.
    
    Authentication priority:
    1. token.json (existing OAuth user token)
    2. OAuth flow via client_secret.json (interactive, opens browser)
    3. Service account JSON key file (last resort for CI/headless)
    
    Returns:
        Credentials object or None if all methods fail.
    """
    # Priority 1: Load existing OAuth token
    creds = _authenticate_via_token()
    if creds and creds.valid:
        return creds

    # Try to refresh expired token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Refreshed expired OAuth token")
            return creds
        except Exception as e:
            logger.warning(f"Failed to refresh token: {e}")
            creds = None

    # Priority 2: Interactive OAuth flow (opens browser)
    if CLIENT_SECRET_PATH.exists():
        logger.info("Starting OAuth flow - browser will open...")
        oauth_creds = _authenticate_via_oauth_flow()
        if oauth_creds:
            return oauth_creds
    else:
        logger.info(
            "No client_secret.json found for OAuth flow. "
            "Skipping to service account..."
        )

    # Priority 3: Service account (headless/CI fallback)
    logger.info("Trying service account authentication...")
    return _authenticate_via_service_account()


def publish_post(
    title: str,
    content: str,
    labels: Optional[List[str]] = None,
    creds: Optional[Credentials] = None,
) -> Optional[Dict]:
    """
    Publish a blog post to Blogger.
    
    Modes (configurable via PUBLISH_MODE in .env):
      - draft     = simpan sebagai draft (default)
      - live      = publish langsung ke blog
      - scheduled = publish otomatis setelah PUBLISH_DELAY_HOURS jam
    
    Cara kerja:
      - draft: insert dengan isDraft=true
      - live: insert sebagai draft, lalu publish via posts.publish()
      - scheduled: insert sebagai draft, lalu posts.publish(publishDate=future)
    
    Args:
        title: The article title.
        content: HTML content of the article.
        labels: Optional list of labels/categories.
        creds: OAuth2 credentials (auto-authenticates if not provided).
        
    Returns:
        API response dict if successful, None otherwise.
    """
    if not BLOGGER_BLOG_ID:
        logger.error("BLOGGER_BLOG_ID is not configured")
        return None

    # Authenticate if credentials not provided
    if not creds:
        creds = authenticate()
        if not creds:
            return None

    try:
        # Build Blogger API v3 service
        service = build("blogger", "v3", credentials=creds)

        from datetime import datetime, timedelta, timezone

        is_draft_mode = PUBLISH_MODE == "draft"
        is_live_mode = PUBLISH_MODE == "live"
        is_scheduled_mode = PUBLISH_MODE == "scheduled"

        # --- Step 1: Insert as draft ---
        post_body: Dict = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "status": "DRAFT",
        }
        if labels:
            post_body["labels"] = labels

        mode_label = {
            "draft": "DRAFT",
            "live": "LIVE",
            "scheduled": f"SCHEDULED (+{PUBLISH_DELAY_HOURS}h)",
        }.get(PUBLISH_MODE, "DRAFT")

        logger.info(
            f"Publishing to Blogger (Blog ID: {BLOGGER_BLOG_ID})..."
        )
        logger.info(f"  Mode: {mode_label}")
        logger.info(f"  Title: {title[:80]}")
        logger.info(f"  Labels: {labels}")
        logger.info(f"  Content length: {len(content)} chars")

        # Insert as draft first (always)
        request = service.posts().insert(
            blogId=BLOGGER_BLOG_ID,
            body=post_body,
            isDraft=True,
        )
        response = request.execute()
        post_id = response.get("id", "unknown")

        logger.info(f"  Draft created: ID {post_id}")

        # --- Step 2: Publish or schedule if not draft mode ---
        if is_live_mode:
            logger.info("  Publishing immediately...")
            publish_request = service.posts().publish(
                blogId=BLOGGER_BLOG_ID,
                postId=post_id,
            )
            response = publish_request.execute()
            logger.info(f"✅ Published LIVE!")
            logger.info(f"  URL: {response.get('url', 'unknown')}")
            logger.info(f"  Status: {response.get('status', 'unknown')}")

        elif is_scheduled_mode and PUBLISH_DELAY_HOURS > 0:
            scheduled_time = datetime.now(timezone.utc) + timedelta(
                hours=PUBLISH_DELAY_HOURS
            )
            publish_date_str = scheduled_time.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
            logger.info(
                f"  Scheduling for: "
                f"{scheduled_time.strftime('%Y-%m-%d %H:%M UTC')}"
            )
            publish_request = service.posts().publish(
                blogId=BLOGGER_BLOG_ID,
                postId=post_id,
                publishDate=publish_date_str,
            )
            response = publish_request.execute()
            logger.info(f"✅ Scheduled! ({PUBLISH_DELAY_HOURS}h from now)")
            logger.info(f"  URL: {response.get('url', 'unknown')}")
            logger.info(f"  Status: {response.get('status', 'unknown')}")

        else:
            logger.info(f"✅ Saved as DRAFT")
            logger.info(f"  URL: {response.get('url', 'unknown')}")

        return response

    except HttpError as e:
        error_details = json.loads(e.content) if e.content else {}
        error_msg = error_details.get("error", {}).get("message", str(e))
        logger.error(f"Blogger API error: {error_msg}")

        if e.resp.status == 401:
            logger.error(
                "Authentication failed. Try deleting token.json and re-authenticating."
            )
        elif e.resp.status == 403:
            logger.error(
                "Access forbidden. Check that your OAuth consent screen "
                "has the Blogger API scope added."
            )
        elif e.resp.status == 404:
            logger.error(
                f"Blog not found. Verify BLOGGER_BLOG_ID = {BLOGGER_BLOG_ID}"
            )
        elif e.resp.status == 429:
            logger.error("Rate limited. Try again later.")

        return None

    except Exception as e:
        logger.error(f"Unexpected error publishing to Blogger: {e}")
        return None


def list_recent_drafts(
    max_results: int = 10, creds: Optional[Credentials] = None
) -> Optional[List[Dict]]:
    """
    List recent draft posts from the blog.
    
    Args:
        max_results: Maximum number of drafts to retrieve.
        creds: OAuth2 credentials.
        
    Returns:
        List of draft posts or None if failed.
    """
    if not BLOGGER_BLOG_ID:
        logger.error("BLOGGER_BLOG_ID is not configured")
        return None

    if not creds:
        creds = authenticate()
        if not creds:
            return None

    try:
        service = build("blogger", "v3", credentials=creds)
        request = service.posts().list(
            blogId=BLOGGER_BLOG_ID,
            status="DRAFT",
            maxResults=max_results,
        )
        response = request.execute()
        items = response.get("items", [])
        logger.info(f"Found {len(items)} draft(s) in Blogger")
        return items

    except HttpError as e:
        logger.error(f"Blogger API error listing drafts: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error listing drafts: {e}")
        return None


def list_recent_posts(
    max_results: int = 10, creds: Optional[Credentials] = None
) -> List[Dict]:
    """
    List recent published posts from the blog (for internal backlink references).
    
    Args:
        max_results: Maximum number of posts to retrieve.
        creds: OAuth2 credentials.
        
    Returns:
        List of post dicts with 'title', 'url', 'id' keys. Empty list on error.
    """
    if not BLOGGER_BLOG_ID:
        return []

    if not creds:
        creds = authenticate()
        if not creds:
            return []

    try:
        service = build("blogger", "v3", credentials=creds)
        request = service.posts().list(
            blogId=BLOGGER_BLOG_ID,
            status="LIVE",
            maxResults=max_results,
        )
        response = request.execute()
        items = response.get("items", [])

        # Extract only what we need for backlink context
        posts = []
        for item in items:
            posts.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "labels": item.get("labels", []),
            })

        logger.info(f"Found {len(posts)} recent published post(s) for backlinks")
        return posts

    except HttpError as e:
        logger.warning(f"Blogger API error listing posts: {e}")
        return []
    except Exception as e:
        logger.warning(f"Unexpected error listing posts: {e}")
        return []


def format_posts_for_backlinks(posts: List[Dict]) -> str:
    """
    Format recent posts as context for the AI to generate backlinks.
    
    Args:
        posts: List of post dicts from list_recent_posts.
        
    Returns:
        Formatted string of articles for the prompt.
    """
    if not posts:
        return "(belum ada artikel terpublished untuk dijadikan backlink)"

    lines = []
    for i, post in enumerate(posts, 1):
        title = post.get("title", "Tanpa Judul")
        url = post.get("url", "")
        labels = ", ".join(post.get("labels", []))
        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        if labels:
            lines.append(f"   Label: {labels}")
        lines.append("")

    return "\n".join(lines)

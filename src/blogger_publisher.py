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
            open_browser=False,
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
    1. token.json (existing OAuth user token - best for CI/automation)
    2. Service account JSON key file (for server-to-server)
    3. OAuth flow via client_secret.json (interactive, first-time setup)
    
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

    # Priority 2: Try service account
    sa_creds = _authenticate_via_service_account()
    if sa_creds:
        return sa_creds

    # Priority 3: Interactive OAuth flow (requires browser)
    return _authenticate_via_oauth_flow()


def publish_draft(
    title: str,
    content: str,
    labels: Optional[List[str]] = None,
    creds: Optional[Credentials] = None,
) -> Optional[Dict]:
    """
    Publish a blog post as DRAFT to Blogger.
    
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

        # Prepare the post body
        post_body: Dict = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "status": "DRAFT",
        }

        if labels:
            post_body["labels"] = labels

        logger.info(
            f"Publishing draft to Blogger (Blog ID: {BLOGGER_BLOG_ID})..."
        )
        logger.info(f"  Title: {title[:80]}")
        logger.info(f"  Labels: {labels}")
        logger.info(f"  Content length: {len(content)} chars")

        # Execute the insert request
        request = service.posts().insert(
            blogId=BLOGGER_BLOG_ID,
            body=post_body,
            isDraft=True,  # Explicitly set as draft
        )
        response = request.execute()

        post_id = response.get("id", "unknown")
        post_url = response.get("url", "unknown")

        logger.info(f"✅ Draft published successfully!")
        logger.info(f"  Post ID: {post_id}")
        logger.info(f"  URL: {post_url}")
        logger.info(f"  Status: {response.get('status', 'unknown')}")

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
            status="draft",
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

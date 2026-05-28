#!/usr/bin/env python3
"""
Beer-style suggestion bot for X (formerly Twitter).

When the bot is mentioned, it replies with a randomly chosen beer style and a
few commercial examples loaded from a BJCP-style ``styleguide.xml`` file.

IMPORTANT — API ACCESS (verified May 2026)
    This bot uses the v2 *filtered stream* endpoint to detect mentions.
    Streaming is a READ feature, not a write one, so the original "post only /
    free tier" rationale was inaccurate. As of February 2026 X moved to a
    pay-per-use model and the old free tier is gone for new developers, so
    running this bot incurs a per-post READ charge for every mention delivered
    by the stream, plus a per-post WRITE charge for each reply. Set a maximum
    spend in the developer console before you run it.

Configuration is entirely via environment variables (nothing secret is stored
in this file). Required:

    X_CONSUMER_KEY, X_CONSUMER_SECRET,
    X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET,
    X_BEARER_TOKEN

Optional:
    BOT_USERNAME      handle to listen for / never reply to  (no leading @)
    STYLEGUIDE_PATH   path to the XML style guide  (default: styleguide.xml)
    BOT_LOG_PATH      log file path                (default: bot.log)
    COOLDOWN_HOURS    min hours between replies to one user (default: 1)
"""

from __future__ import annotations

import logging
import os
import random
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import tweepy

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BOT_USERNAME = os.environ.get("BOT_USERNAME", "your_twitter_bot_handle").lstrip("@")
STYLEGUIDE_PATH = Path(os.environ.get("STYLEGUIDE_PATH", "styleguide.xml"))
LOG_PATH = os.environ.get("BOT_LOG_PATH", "bot.log")
COOLDOWN = timedelta(hours=float(os.environ.get("COOLDOWN_HOURS", "1")))
MAX_TWEET_LEN = 280

REQUIRED_ENV = (
    "X_CONSUMER_KEY",
    "X_CONSUMER_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET",
    "X_BEARER_TOKEN",
)

log = logging.getLogger("beer_bot")


# --------------------------------------------------------------------------- #
# Setup helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Rotating file log (5 MB x 3) plus a console stream."""
    fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(fmt)

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    log.setLevel(logging.INFO)
    log.addHandler(file_handler)
    log.addHandler(console)


def load_credentials() -> dict[str, str]:
    """Read API credentials from the environment, failing loudly if absent."""
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)
    return {name: os.environ[name] for name in REQUIRED_ENV}


def load_beer_styles(file_path: Path) -> dict[str, dict]:
    """
    Parse a BJCP-style XML guide into {subcat_id: {"name": str, "examples": [str]}}.

    Returns an empty dict on any structural/IO problem (logged), so the caller
    can decide whether to abort.
    """
    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        log.error("Style guide not found: %s", file_path)
        return {}
    except ET.ParseError as exc:
        log.error("Could not parse %s: %s", file_path, exc)
        return {}

    root = tree.getroot()
    beer_styles: dict[str, dict] = {}
    for subcategory in root.findall(".//category/subcategory"):
        subcat_id = subcategory.get("id")
        name_el = subcategory.find("name")
        if subcat_id is None or name_el is None or not (name_el.text or "").strip():
            continue  # skip malformed entries rather than crashing

        examples_el = subcategory.find("examples")
        examples: list[str] = []
        if examples_el is not None and examples_el.text:
            examples = [e.strip() for e in examples_el.text.split(",") if e.strip()]

        beer_styles[subcat_id] = {"name": name_el.text.strip(), "examples": examples}

    log.info("Loaded %d beer styles from %s", len(beer_styles), file_path)
    return beer_styles


def random_beer(beer_styles: dict[str, dict]) -> tuple[str, list[str]]:
    info = random.choice(list(beer_styles.values()))
    return info["name"], info["examples"]


# --------------------------------------------------------------------------- #
# Stream listener
# --------------------------------------------------------------------------- #
class MentionListener(tweepy.StreamingClient):
    """Listens for mentions and replies with a beer suggestion."""

    def __init__(self, bearer_token, *, poster, beer_styles, bot_username):
        super().__init__(bearer_token)
        self.poster = poster
        self.beer_styles = beer_styles
        self.bot_username = bot_username.lower()
        # user_id -> last reply time; pruned every check so it stays bounded.
        self._last_reply: dict[int, datetime] = {}

    def _can_respond(self, user_id: int) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - COOLDOWN
        # Drop entries older than the cooldown so the dict can't grow unbounded.
        self._last_reply = {u: t for u, t in self._last_reply.items() if t > cutoff}
        if user_id in self._last_reply:
            return False
        self._last_reply[user_id] = now
        return True

    def on_response(self, response):
        """
        Called for every matching post. ``response`` is a StreamResponse with
        .data (the tweet) and .includes (where expanded users live). This is the
        only place the author's username is available.
        """
        tweet = response.data
        if tweet is None:
            return

        users = {u.id: u for u in (response.includes or {}).get("users", [])}
        author = users.get(tweet.author_id)
        username = author.username if author else None

        if tweet.author_id is None:
            log.warning("Tweet %s had no author_id (check expansions).", tweet.id)
            return
        if username and username.lower() == self.bot_username:
            return  # never reply to ourselves -> avoids feedback loops
        if not self._can_respond(tweet.author_id):
            log.info("Cooldown active for @%s", username or tweet.author_id)
            return

        name, examples = random_beer(self.beer_styles)
        examples_str = ", ".join(examples) if examples else "no widely-known examples"
        mention = f"@{username} " if username else ""
        text = f"{mention}Try a {name}! Examples include: {examples_str}. Cheers! 🍻"
        if len(text) > MAX_TWEET_LEN:
            text = text[: MAX_TWEET_LEN - 1].rstrip() + "…"

        try:
            self.poster.create_tweet(text=text, in_reply_to_tweet_id=tweet.id)
            log.info("Replied to @%s with style '%s'", username or tweet.author_id, name)
        except tweepy.TweepyException as exc:
            log.error("Failed to reply to tweet %s: %s", tweet.id, exc)

    # --- stream-level error hooks (tweepy auto-reconnects on recoverable ones) ---
    def on_request_error(self, status_code):
        log.error("Stream request error: HTTP %s", status_code)

    def on_connection_error(self):
        log.error("Stream connection error; tweepy will attempt to reconnect.")

    def on_errors(self, errors):
        log.error("Stream payload errors: %s", errors)


# --------------------------------------------------------------------------- #
# Rule management & entry point
# --------------------------------------------------------------------------- #
def reset_rules(stream: tweepy.StreamingClient, rule_value: str) -> None:
    """Delete any existing rules, then install exactly the one we want."""
    existing = stream.get_rules()
    ids = [r.id for r in (existing.data or [])]
    if ids:
        stream.delete_rules(ids)
        log.info("Deleted %d stale stream rule(s).", len(ids))
    stream.add_rules(tweepy.StreamRule(value=rule_value))


def main() -> None:
    configure_logging()
    creds = load_credentials()

    beer_styles = load_beer_styles(STYLEGUIDE_PATH)
    if not beer_styles:
        log.error("No beer styles available; aborting.")
        sys.exit(1)

    # Posting uses OAuth 1.0a user context; the stream uses the bearer token.
    poster = tweepy.Client(
        bearer_token=creds["X_BEARER_TOKEN"],
        consumer_key=creds["X_CONSUMER_KEY"],
        consumer_secret=creds["X_CONSUMER_SECRET"],
        access_token=creds["X_ACCESS_TOKEN"],
        access_token_secret=creds["X_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )

    stream = MentionListener(
        creds["X_BEARER_TOKEN"],
        poster=poster,
        beer_styles=beer_styles,
        bot_username=BOT_USERNAME,
    )

    rule_value = f"@{BOT_USERNAME} -is:retweet -from:{BOT_USERNAME}"
    reset_rules(stream, rule_value)
    log.info("Starting stream with rule: %s", rule_value)

    try:
        stream.filter(
            expansions=["author_id"],
            tweet_fields=["author_id", "created_at"],
            user_fields=["username"],
        )
    except KeyboardInterrupt:
        log.info("Interrupted by user; shutting down.")
    finally:
        stream.disconnect()


if __name__ == "__main__":
    main()

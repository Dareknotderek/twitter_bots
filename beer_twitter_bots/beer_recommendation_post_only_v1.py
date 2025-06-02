#!/usr/bin/env python3

import os
import sys
import time
import random
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import tweepy
import schedule
import xml.etree.ElementTree as ET

# Constants
DEFAULT_TWEET_INTERVAL_HOURS: int = 6
LOG_FILE_PATH: Path = Path(__file__).parent / "bot.log"
BEER_STYLES_XML_PATH: Path = Path(__file__).parent / "styleguide.xml"


def setup_logging(log_path: Path) -> logging.Logger:
    """
    Configure and return a logger with a RotatingFileHandler.

    :param log_path: Path to the log file.
    :return: Configured logger.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def get_twitter_client(logger: logging.Logger) -> tweepy.Client:
    """
    Authenticate with the Twitter API and return a Tweepy client.

    :param logger: Logger for error reporting.
    :return: Authenticated Tweepy client.
    """
    # Retrieve environment variables
    consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
    consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')

    # Check for missing credentials
    credentials = {
        'TWITTER_CONSUMER_KEY': consumer_key,
        'TWITTER_CONSUMER_SECRET': consumer_secret,
        'TWITTER_ACCESS_TOKEN': access_token,
        'TWITTER_ACCESS_TOKEN_SECRET': access_token_secret,
        'TWITTER_BEARER_TOKEN': bearer_token,
    }
    missing = [name for name, value in credentials.items() if not value]
    if missing:
        logger.error(f"Missing Twitter credentials: {', '.join(missing)}")
        sys.exit(1)

    # Create and return client
    return tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )


def load_beer_styles_from_xml(file_path: Path, logger: logging.Logger) -> Dict[str, Dict[str, List[str]]]:
    """
    Load beer styles from an XML file into a dictionary.

    :param file_path: Path to the XML file.
    :param logger: Logger for error reporting.
    :return: A dictionary mapping subcategory IDs to name and examples.
    """
    if not file_path.exists():
        logger.error(f"XML file not found: {file_path}")
        sys.exit(1)

    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        logger.error(f"Error parsing XML file: {e}")
        sys.exit(1)

    root = tree.getroot()
    beer_styles: Dict[str, Dict[str, List[str]]] = {}
    for category in root.findall(".//category"):
        for subcategory in category.findall("subcategory"):
            subcat_id: Optional[str] = subcategory.get("id")
            if not subcat_id:
                continue

            name_elem = subcategory.find("name")
            name: str = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed"
            examples_elem = subcategory.find("examples")
            if examples_elem is not None and examples_elem.text:
                examples = [ex.strip() for ex in examples_elem.text.split(",") if ex.strip()]
            else:
                examples = []
            beer_styles[subcat_id] = {"name": name, "examples": examples}

    return beer_styles


def get_random_beer(beer_styles: Dict[str, Dict[str, List[str]]], logger: logging.Logger) -> Tuple[str, List[str]]:
    """
    Select a random beer style from the provided dictionary.

    :param beer_styles: Dictionary of beer styles.
    :param logger: Logger for debugging.
    :return: A tuple of (beer_name, examples).
    """
    if not beer_styles:
        logger.error("Beer styles dictionary is empty.")
        sys.exit(1)

    beer_id = random.choice(list(beer_styles.keys()))
    beer_info = beer_styles[beer_id]
    logger.debug(f"Selected beer style ID: {beer_id}")
    return beer_info["name"], beer_info["examples"]


def tweet_beer_recommendation(client: tweepy.Client, beer_styles: Dict[str, Dict[str, List[str]]], logger: logging.Logger) -> None:
    """
    Construct and send a tweet recommending a random beer.

    :param client: The Tweepy client.
    :param beer_styles: Dictionary of beer styles.
    :param logger: Logger for info and error reporting.
    """
    beer_name, examples = get_random_beer(beer_styles, logger)
    if examples:
        examples_str = ", ".join(examples)
        tweet_content = f"Try a {beer_name}! Examples include: {examples_str}. Cheers! 🍻"
    else:
        tweet_content = f"Try a {beer_name}! Cheers! 🍻"

    try:
        client.create_tweet(text=tweet_content)
        logger.info(f"Tweeted: {tweet_content}")
    except tweepy.TweepyException as e:
        logger.error(f"Error while tweeting: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            logger.error(f"Twitter response: {e.response.text}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")


def main() -> None:
    # Initialize logger
    logger = setup_logging(LOG_FILE_PATH)

    # Initialize Twitter client
    client = get_twitter_client(logger)

    # Load beer styles
    beer_styles = load_beer_styles_from_xml(BEER_STYLES_XML_PATH, logger)
    logger.info(f"Loaded {len(beer_styles)} beer styles from {BEER_STYLES_XML_PATH}")
    if not beer_styles:
        logger.error("No beer styles loaded from XML.")
        sys.exit(1)

    # Determine tweet interval
    interval_hours = DEFAULT_TWEET_INTERVAL_HOURS
    env_interval = os.environ.get('TWEET_INTERVAL_HOURS')
    if env_interval:
        try:
            interval_hours = int(env_interval)
        except ValueError:
            logger.warning(f"Invalid TWEET_INTERVAL_HOURS value '{env_interval}', using default {DEFAULT_TWEET_INTERVAL_HOURS} hours.")

    # Schedule tweeting
    schedule.every(interval_hours).hours.do(tweet_beer_recommendation, client, beer_styles, logger)

    # Run first tweet immediately before entering loop
    tweet_beer_recommendation(client, beer_styles, logger)

    # Scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Unhandled exception in scheduler: {e}")


if __name__ == '__main__':
    main()

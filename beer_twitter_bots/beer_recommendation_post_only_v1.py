import os
import sys
import time
import random
import logging
import tweepy
import schedule
import xml.etree.ElementTree as ET
from logging.handlers import RotatingFileHandler

# Constants
BEER_STYLES_XML_PATH = 'styleguide.xml'
TWEET_INTERVAL_HOURS = int(os.environ.get('TWEET_INTERVAL_HOURS', 6))

# Set up logging with RotatingFileHandler
handler = RotatingFileHandler(
    'bot.log',  # Log file name
    maxBytes=5 * 1024 * 1024,  # Max size before rollover (5MB)
    backupCount=3  # Number of backup files to keep
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Twitter API keys from environment variables
CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

# Check if any of the credentials are missing
credentials = {
    'TWITTER_CONSUMER_KEY': CONSUMER_KEY,
    'TWITTER_CONSUMER_SECRET': CONSUMER_SECRET,
    'TWITTER_ACCESS_TOKEN': ACCESS_TOKEN,
    'TWITTER_ACCESS_TOKEN_SECRET': ACCESS_TOKEN_SECRET,
    'TWITTER_BEARER_TOKEN': BEARER_TOKEN,
}

missing_credentials = [key for key, value in credentials.items() if not value]
if missing_credentials:
    logger.error(f"Missing Twitter credentials: {', '.join(missing_credentials)}")
    sys.exit(1)

# Twitter Authenticate
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)


def load_beer_styles_from_xml(file_path):
    """
    Load beer styles from an XML file.

    :param file_path: Path to the XML file.
    :return: Dictionary of beer styles.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Error parsing XML file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"XML file not found: {file_path}")
        sys.exit(1)

    beer_styles = {}
    for category in root.findall(".//category"):
        for subcategory in category.findall("subcategory"):
            subcat_id = subcategory.get("id")
            name_element = subcategory.find("name")
            name = name_element.text if name_element is not None else "Unnamed"
            examples_element = subcategory.find("examples")
            if examples_element is not None and examples_element.text is not None:
                examples = [ex.strip() for ex in examples_element.text.split(",")]
            else:
                examples = []
            beer_styles[subcat_id] = {"name": name, "examples": examples}
    return beer_styles


beer_styles = load_beer_styles_from_xml(BEER_STYLES_XML_PATH)
logger.info(f"Loaded {len(beer_styles)} beer styles from {BEER_STYLES_XML_PATH}")

if not beer_styles:
    logger.error("No beer styles loaded from XML.")
    sys.exit(1)


def get_random_beer():
    """
    Select a random beer style.

    :return: Tuple containing the beer name and a list of examples.
    """
    beer_id = random.choice(list(beer_styles.keys()))
    beer_info = beer_styles[beer_id]
    logger.debug(f"Selected beer style ID: {beer_id}")
    return beer_info["name"], beer_info["examples"]


def tweet_beer_recommendation():
    """
    Tweet a random beer recommendation.
    """
    beer_name, examples = get_random_beer()
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
            logger.error(f"Response text: {e.response.text}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")



def main():
    # Schedule the tweet every TWEET_INTERVAL_HOURS hours
    schedule.every(TWEET_INTERVAL_HOURS).hours.do(tweet_beer_recommendation)
    # Run the first tweet immediately
    tweet_beer_recommendation()

    # Run the scheduler
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")


if __name__ == '__main__':
    main()

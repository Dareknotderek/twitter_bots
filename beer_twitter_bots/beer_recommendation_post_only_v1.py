import tweepy
import random
import logging
from logging.handlers import RotatingFileHandler
import xml.etree.ElementTree as ET
import schedule
import time



# Set up logging with RotatingFileHandler
handler = RotatingFileHandler(
    'bot.log',  # Log file name
    maxBytes=5*1024*1024,  # Max size before rollover (5MB)
    backupCount=3  # Number of backup files to keep
)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Twitter API keys
CONSUMER_KEY = 'Your Consumer'
CONSUMER_SECRET = 'Your Consumer Secret'
ACCESS_TOKEN = 'Your Access Token'
ACCESS_TOKEN_SECRET = 'Your Access Token Secret'
BEARER_TOKEN = 'Your Bearer Token'


#Twitter Authenticate
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Read the dictionary from styleguide.xml
def load_beer_styles_from_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    beer_styles = {}
    for category in root.findall(".//category"):
        for subcategory in category.findall("subcategory"):
            subcat_id = subcategory.get("id")
            name = subcategory.find("name").text
            examples_element = subcategory.find("examples")
            if examples_element is not None and examples_element.text is not None:
                examples = examples_element.text.split(", ")
            else:
                examples = []
            beer_styles[subcat_id] = {"name": name, "examples": examples}
    return beer_styles

beer_styles = load_beer_styles_from_xml('styleguide.xml')

# Function to select a random beer style
def get_random_beer():
    beer_id = random.choice(list(beer_styles.keys()))
    beer_info = beer_styles[beer_id]
    return beer_info["name"], beer_info["examples"]

# Function to tweet a random beer recommendation
def tweet_beer_recommendation():
    beer_name, examples = get_random_beer()
    examples_str = ", ".join(examples) if examples else "No examples available"
    tweet_content = f"Try a {beer_name}! Examples include: {examples_str}. Cheers! 🍻"
    try:
        client.create_tweet(text=tweet_content)
        logging.info(f"Tweeted: {tweet_content}")
    except tweepy.TweepyException as e:
        logging.error(f"Error while tweeting: {e}")
        logging.error(e.response.text)

# Schedule the tweet every 6 hours
schedule.every(6).hours.do(tweet_beer_recommendation)

# Run the scheduler
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("Bot stopped by user")

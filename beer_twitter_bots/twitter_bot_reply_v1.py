#This is still an experimental version and in development. X's free access API does not allow retreives, only posts, hence the post only bot. Documentation for this version of the bot
#will be added once it has been tested and proven stable. 

import tweepy
import random
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import os
import xml.etree.ElementTree as ET



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
CONSUMER_KEY = 'YOUR CONSUMER KEY'
CONSUMER_SECRET = 'YOUR CONSUMER SECRET'
ACCESS_TOKEN = 'YOUR ACCESS TOKEN'
ACCESS_TOKEN_SECRET = 'YOUR ACCESS TOKEN SECRET'
BEARER_TOKEN = 'YOUR BEARER TOKEN'


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

#Rate limit check for user:
user_last_interaction = {}

def can_respond(user_id):
    now = datetime.now()
    if user_id in user_last_interaction:
        last_interaction = user_last_interaction[user_id]
        if now - last_interaction < timedelta(hours=1):
            return False
    user_last_interaction[user_id] = now
    return True

#StreamListener Class / can respond / response
class MyStreamListener(tweepy.StreamingClient):

    def on_tweet(self, tweet):
        user_id = tweet.author_id
        if can_respond(user_id):
            beer_name, examples = get_random_beer()
            examples_str = ", ".join(examples) if examples else "No examples available"
            response = f"@{tweet.author.username} Try a {beer_name}! Examples include: {examples_str}. Cheers! 🍻"
            client.create_tweet(text=response, in_reply_to_tweet_id=tweet.id)
            logging.info(f"Responded to @{tweet.author.username} with {beer_name} and examples: {examples_str}")
        else:
            logging.info(f"Rate limit exceeded for @{tweet.author.username}")

    def on_errors(self, errors):
        logging.error(f"Encountered errors: {errors}")

# Set up the stream
streaming_client = MyStreamListener(bearer_token=BEARER_TOKEN)
streaming_client.add_rules(tweepy.StreamRule(value='@your_twitter_bot_handle'))
streaming_client.filter()

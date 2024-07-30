# Beer Recommendation Twitter Bot (Post Only)
This Python script is a Twitter bot that tweets random beer recommendations every six hours -- but you can adjust it to whatever you'd like. The beer styles and examples are loaded from an XML file (styleguide.xml). The bot uses the Tweepy library to interact with the Twitter API and the schedule library to manage tweet intervals.

## Features
- Tweets a random beer style recommendation every six hours.
- Loads beer styles and examples from an XML file.
- Uses rotating file handler for logging.
- Error handling for Twitter API interactions.
  
## Prerequisites
- Python 3.7+
- Twitter Developer account with API keys and tokens
- tweepy library
- schedule library
- XML file (styleguide.xml) containing beer styles and examples -- provided in this repository.

## Installation
Clone the repository:
```
git clone https://github.com/yourusername/beer-recommendation-bot.git
cd beer-recommendation-bot
```

Install the required Python packages:
```
pip install tweepy schedule
```

Place your `styleguide.xml` or whatever you name your xml file in the same directory as the script. Be sure to update the code to reflect your xml file's name. 

## Configuration
Replace the placeholder values for the Twitter API keys and tokens in the script:
```
CONSUMER_KEY = 'Your Consumer Key'
CONSUMER_SECRET = 'Your Consumer Secret'
ACCESS_TOKEN = 'Your Access Token'
ACCESS_TOKEN_SECRET = 'Your Access Token Secret'
BEARER_TOKEN = 'Your Bearer Token'
```

## Usage
Run the script by calling whatever you've named your version of this bot in a terminal or command prompt. Ensure you are in the correct directory before calling. 
```
python beer_twitter_bot_post_only_v1.py
```
The bot will tweet a random beer style recommendation every six hours or whatever interval you have set. 

## Logging
The bot uses a rotating file handler to log information and errors. Logs are saved in a bot.log file and up to three backup log files are kept. 

## XML File Structure
The styleguide.xml file should have the following structure:
```
<styles>
    <category>
        <subcategory id="1A">
            <name>Example Beer Style</name>
            <examples>Example Beer 1, Example Beer 2</examples>
        </subcategory>
        <!-- More subcategories -->
    </category>
    <!-- More categories -->
</styles>
```

## Stopping the Bot
To stop the bot, simply interrupt the script (e.g., press Ctrl+C in the terminal). The bot will log that it was stopped by the user.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## Acknowledgements
Special thanks to the developers of Tweepy and Schedule libraries.
Additionally, thank you to [Nick Nichols](https://github.com/nnichols) and [jcv](https://github.com/jcvernaleo/) for their contributions to this bot and the beer coding scene more generally. 

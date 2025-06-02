# Beer Tweet Bot

A simple Python bot that periodically tweets a random beer recommendation using Twitter's API. It loads beer styles from an XML file (`styleguide.xml`), selects a random style, and formats a tweet recommending the style with example beers. Tweets are sent at a configurable interval and logged using a rotating file handler.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)

   * [Environment Variables](#environment-variables)
   * [Beer Styles XML](#beer-styles-xml)
   * [Tweet Interval](#tweet-interval)
5. [Usage](#usage)
6. [Project Structure](#project-structure)
7. [Logging](#logging)
8. [Extending the Bot](#extending-the-bot)
9. [Contributing](#contributing)
10. [License](#license)

---

## Features

* Loads beer styles from an XML file, including category, subcategory, beer names, and example brews.
* Selects a random beer style and composes a tweet recommending it.
* Schedules tweets at a configurable hourly interval (default: 6 hours).
* Logs events (info, errors) to a rotating log file (`bot.log`), with automatic rollover when file size exceeds 5 MB.
* Gracefully handles missing credentials or XML parsing errors, exiting with a clear error message.

---

## Prerequisites

* Python 3.7+
* A Twitter developer account with API credentials (consumer key/secret, access token/secret, bearer token).
* `styleguide.xml` containing beer style definitions.

**Python Dependencies** (install via `pip`):

* `tweepy` (for Twitter API access)
* `schedule` (for scheduling periodic tasks)

Example install command:

```bash
pip install tweepy schedule
```

---

## Installation

1. **Clone the repository**

   ```bash
   ```

git clone [https://github.com/your-username/beer-tweet-bot.git](https://github.com/your-username/beer-tweet-bot.git)
cd beer-tweet-bot

````

2. **Verify `styleguide.xml`**  
Ensure `styleguide.xml` is present in the project root and follows the expected format (see [Beer Styles XML](#beer-styles-xml)).

3. **Install dependencies**

```bash
pip install -r requirements.txt
````

> **Note:** If you don’t have a `requirements.txt`, install `tweepy` and `schedule` manually:
>
> ```bash
> pip install tweepy schedule
> ```

---

## Configuration

### Environment Variables

Before running the bot, set the following environment variables with your Twitter API credentials:

```bash
export TWITTER_CONSUMER_KEY="your_consumer_key"
export TWITTER_CONSUMER_SECRET="your_consumer_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"
export TWITTER_BEARER_TOKEN="your_bearer_token"
```

If any credential is missing or empty, the bot will log an error and exit.

---

### Beer Styles XML

By default, the bot looks for `styleguide.xml` in the same directory as the script. The XML structure should resemble:

```xml
<root>
  <category>
    <subcategory id="01">
      <name>American Pale Ale (APA)</name>
      <examples>Lagunitas IPA, Sierra Nevada Pale Ale, Founders All Day IPA</examples>
    </subcategory>
    <subcategory id="02">
      <name>Stout</name>
      <examples>Guinness Draught, Samuel Smith’s Oatmeal Stout</examples>
    </subcategory>
    <!-- More categories & subcategories -->
  </category>
  <!-- More categories -->
</root>
```

Each `<subcategory>` must have an `id` attribute, a `<name>` child, and an optional `<examples>` child (comma-separated list of beer names).

---

### Tweet Interval

The bot sends a tweet immediately upon start, then repeats every `TWEET_INTERVAL_HOURS` hours.

* **Default interval:** 6 hours
* **Override:** Set `TWEET_INTERVAL_HOURS` environment variable to an integer (e.g., `export TWEET_INTERVAL_HOURS=3`).

If `TWEET_INTERVAL_HOURS` is invalid (non-integer), the bot logs a warning and continues using the default.

---

## Usage

Execute the main script (`beer_tweet_bot.py`). For example:

```bash
python beer_tweet_bot.py
```

Once started:

* The first beer recommendation tweet is sent immediately.
* Subsequent tweets occur at the configured interval.
* Log messages appear in `bot.log`. If you stop the script (e.g., `Ctrl+C`), it logs "Bot stopped by user" and exits.

### Running as a Background Process (Optional)

On Linux/macOS, you can run the bot in the background:

```bash
nohup python beer_tweet_bot.py > /dev/null 2>&1 &
```

This will detach the process. Check `bot.log` for activity.

If you want to run on a schedule (e.g., systemd service or cron job), ensure the process remains active.

---

## Project Structure

```
beer-tweet-bot/
├── README.md
├── beer_tweet_bot.py      # Main script (refactored version)
├── styleguide.xml         # Beer styles definitions
├── bot.log                # Rotating log file (created at runtime)
├── requirements.txt       # Python dependencies (tweepy, schedule)
└── LICENSE                # License file (optional)
```

* `beer_tweet_bot.py`: Contains the bot logic, including logging setup, Twitter authentication, XML parsing, random selection, and scheduling.
* `styleguide.xml`: Defines beer categories/subcategories with IDs, names, and example beers.
* `bot.log`: Created automatically; uses a rotating handler (max 5 MB, 3 backup files).

---

## Logging

The bot uses Python's `logging` module with a `RotatingFileHandler`:

* **Log file:** `bot.log` in the project directory.
* **Max size per file:** 5 MB
* **Backup count:** 3 (older logs are archived as `bot.log.1`, `bot.log.2`, etc.)

Log levels:

* **INFO:** Startup/shutdown events, successful tweets, loaded beer count.
* **DEBUG:** Internal details like selected beer style ID (only visible if you change the logger level to `DEBUG`).
* **ERROR:** Missing credentials, XML parsing errors, tweeting failures, unexpected exceptions.

To see debug messages, modify `logger.setLevel(logging.DEBUG)` in `setup_logging()`.

---

## Extending the Bot

* **Add new XML fields:** Modify `load_beer_styles_from_xml()` to capture additional attributes (e.g., ABV, IBU).
* **Customize tweet format:** Update `tweet_beer_recommendation()` to include hashtags, emojis, or dynamic content (e.g., current weather).
* **Support multiple XML sources:** Allow passing multiple file paths or merge multiple styleguides.
* **Image attachments:** Enhance with `tweepy.Client.create_tweet(media_ids=[...], text=...)` if you have beer images.
* **Unit tests:** Add tests for XML parsing, random selection, and tweet content generation.

---

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit (`git commit -m "Add some feature"`).
4. Push to your fork (`git push origin feature/YourFeature`).
5. Open a Pull Request.

Please ensure:

* Code follows PEP 8 guidelines.
* New functionality includes appropriate tests (if applicable).
* README is updated if behavior changes.

---

Enjoy sharing beer recommendations on Twitter! Cheers! “🍻”

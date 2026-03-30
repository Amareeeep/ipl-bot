import os
import time
import logging
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.apihelper import ApiTelegramException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read environment variables
BOT_TOKEN = os.getenv("8716019997:AAEYodES3bkjOXGxRXvC1D-wA65xqUM8jBk")
CHANNEL_ID = os.getenv("@nextballLive")  # e.g., "@my_channel"

if not BOT_TOKEN or not CHANNEL_ID:
    logging.error("Missing environment variables. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Global state
last_ball = ""
over_data = []
last_comment = ""

def fetch_commentary():
    """Fetch the latest commentary line from Cricbuzz."""
    url = "https://www.cricbuzz.com/live-cricket-scores"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Try multiple possible selectors (update as needed based on actual page structure)
    # Common classes: 'cb-com-ln', 'cb-comm-ln', or 'comment-text'
    selectors = [
        "div.cb-comm-ln",
        "div.cb-com-ln",
        "div.comment-text",
        "div.live-commentary-item div.comment"
    ]

    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            return elem.get_text(strip=True)

    logging.warning("No commentary element found.")
    return None

def parse_ball_number(comment):
    """Extract ball number from commentary text."""
    # Typical format: "0.1 ..." or "19.6 ..."
    words = comment.split()
    if words:
        first = words[0]
        # Check if it matches a ball number pattern (digits.digits)
        if '.' in first and all(part.isdigit() for part in first.split('.')):
            return first
    return ""

def detect_event(comment):
    """Detect event type and return (event_text, run_symbol)."""
    c = comment.lower()

    if "four" in c or "4 runs" in c:
        return "🔥 FOUR!!!", "4"
    elif "six" in c or "6 runs" in c:
        return "💣 SIX!!!", "6"
    elif "out" in c or "wicket" in c:
        return "💀 WICKET!!!", "W"
    elif "wide" in c:
        return "⚠️ WIDE", "Wd"
    elif "no ball" in c:
        return "🚫 NO BALL", "Nb"
    elif "1 run" in c:
        return "⚡ 1 RUN", "1"
    elif "2 runs" in c:
        return "⚡ 2 RUNS", "2"
    elif "3 runs" in c:
        return "⚡ 3 RUNS", "3"
    else:
        return "⚡ DOT BALL", "0"

def send_ball_update(ball, event, comment):
    """Send a single ball update to the channel."""
    msg = f"""
🎯 {ball}
{event}
📝 {comment}
"""
    try:
        bot.send_message(CHANNEL_ID, msg)
        logging.info(f"Sent update for {ball}")
    except ApiTelegramException as e:
        logging.error(f"Telegram API error: {e}")

def send_over_summary():
    """Send summary of the completed over."""
    global over_data
    if not over_data:
        return

    msg = f"""
🔥 OVER COMPLETE

⚡ This Over: {' '.join(over_data)}
"""
    try:
        bot.send_message(CHANNEL_ID, msg)
        logging.info("Sent over summary")
    except ApiTelegramException as e:
        logging.error(f"Telegram API error: {e}")

    over_data = []

def run_bot():
    """Main loop to fetch and send updates."""
    global last_ball, last_comment, over_data

    logging.info("🔥 PRO BOT RUNNING 🔥")

    while True:
        try:
            comment = fetch_commentary()

            if comment and comment != last_comment:
                ball = parse_ball_number(comment)

                # Only process if we got a valid ball number and it's new
                if ball and ball != last_ball:
                    event, run = detect_event(comment)
                    over_data.append(run)

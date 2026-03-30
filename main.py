import os
import time
import logging
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.apihelper import ApiTelegramException

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BOT_TOKEN = ("8716019997:AAEYodES3bkjOXGxRXvC1D-wA65xqUM8jBk")
CHANNEL_ID = ("@nextballLive")

if not BOT_TOKEN or not CHANNEL_ID:
    logging.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID")
    raise SystemExit(1)

bot = telebot.TeleBot(BOT_TOKEN)

last_ball = ""
last_comment = ""
over_data = []


def get_live_commentary_url():
    url = "https://www.cricbuzz.com/live-cricket-scores"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch live scores page: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Try to find a "Full Commentary" link first
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True).lower()
        href = a["href"]

        if "full commentary" in text and "/live-cricket-full-commentary/" in href:
            if href.startswith("http"):
                return href
            return "https://www.cricbuzz.com" + href

    logging.warning("No live full commentary link found")
    return None


def fetch_commentary():
    headers = {"User-Agent": "Mozilla/5.0"}

    commentary_url = get_live_commentary_url()
    if not commentary_url:
        return None

    try:
        response = requests.get(commentary_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch commentary page: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Try common containers
    selectors = [
        "div.cb-com-ln",
        "div.cb-comm-ln",
        "p.cb-com-ln",
        "div.commentary-text",
        "div.commtext",
    ]

    for selector in selectors:
        elems = soup.select(selector)
        for elem in elems:
            text = elem.get_text(" ", strip=True)
            if text and len(text) > 8:
                return text

    # fallback: scan visible text blocks for ball-like strings
    for tag in soup.find_all(["div", "p", "span"]):
        text = tag.get_text(" ", strip=True)
        if text and "." in text and len(text) > 15:
            parts = text.split()
            first = parts[0] if parts else ""
            if "." in first:
                nums = first.split(".")
                if len(nums) == 2 and nums[0].isdigit() and nums[1].isdigit():
                    return text

    logging.warning("No live commentary found on right now")
    return None

def parse_ball_number(comment):
    words = comment.split()
    for word in words[:5]:
        if "." in word:
            parts = word.split(".")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return word
    return ""


def detect_event(comment):
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
    elif "3 runs" in c:
        return "⚡ 3 RUNS", "3"
    elif "2 runs" in c:
        return "⚡ 2 RUNS", "2"
    elif "1 run" in c:
        return "⚡ 1 RUN", "1"
    else:
        return "⚡ DOT BALL", "0"


def send_ball_update(ball, event, comment):
    msg = f"🎯 {ball}\n{event}\n📝 {comment}"
    try:
        bot.send_message(CHANNEL_ID, msg)
        logging.info(f"Sent update for {ball}")
    except ApiTelegramException as e:
        logging.error(f"Telegram send error: {e}")


def send_over_summary():
    global over_data

    if not over_data:
        return

    msg = f"🔥 OVER COMPLETE\n\n⚡ This Over: {' '.join(over_data)}"
    try:
        bot.send_message(CHANNEL_ID, msg)
        logging.info("Sent over summary")
    except ApiTelegramException as e:
        logging.error(f"Telegram send error: {e}")

    over_data = []


def run_bot():
    global last_ball, last_comment, over_data

    logging.info("🔥 PRO BOT RUNNING 🔥")

    while True:
        try:
            comment = fetch_commentary()

            # 👇 agar commentary nahi mili toh skip
            if not comment:
                logging.info("No live commentary right now...")
                time.sleep(15)
                continue

            # 👇 new comment check
            if comment != last_comment:
                ball = parse_ball_number(comment)

                if ball and ball != last_ball:
                    event, run = detect_event(comment)

                    over_data.append(run)
                    send_ball_update(ball, event, comment)

                    if ball.endswith(".6"):
                        send_over_summary()

                    last_ball = ball

                last_comment = comment

            time.sleep(5)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run_bot()

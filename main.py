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


def fetch_commentary():
    url = "https://www.cricbuzz.com/live-cricket-scores"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    selectors = [
        "div.cb-comm-ln",
        "div.cb-com-ln",
        "div.comment-text",
        "div.live-commentary-item div.comment",
    ]

    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(" ", strip=True)
            if text:
                return text

    logging.warning("No commentary element found")
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

            if comment and comment != last_comment:
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

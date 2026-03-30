import requests
from bs4 import BeautifulSoup
import time
import telebot
import re

BOT_TOKEN = "8716019997:AAEYodES3bkjOXGxRXvC1D-wA65xqUM8jBk"
CHANNEL_ID = "@nextballLive"

bot = telebot.TeleBot(BOT_TOKEN)

last_ball = ""
over_data = []


# ---------------- FETCH (CRICBUZZ BASIC) ---------------- #
def fetch_data():
    try:
        url = "https://www.cricbuzz.com/live-cricket-scores"
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        comm = soup.select_one("div.cb-comm-ln")
        score = soup.select_one("div.cb-lv-scrs-col")

        if comm and score:
            return comm.get_text(strip=True), score.get_text(strip=True)
    except:
        return None, None

    return None, None


# ---------------- EVENT ---------------- #
def detect_event(text):
    t = text.lower()

    if "four" in t:
        return "🔥 FOUR!!!", "4"
    elif "six" in t:
        return "💣 SIX!!!", "6"
    elif "out" in t:
        return "💀 WICKET!!!", "W"
    elif "wide" in t:
        return "⚠️ WIDE", "Wd"
    elif "no ball" in t:
        return "🚫 NO BALL", "Nb"
    elif "1 run" in t:
        return "⚡ 1 RUN", "1"
    elif "2 runs" in t:
        return "⚡ 2 RUNS", "2"
    else:
        return "⚡ DOT BALL", "0"


# ---------------- PLAYER EXTRACT ---------------- #
def extract_players(text):
    try:
        first = text.split(",")[0]
        if " to " in first:
            bowler, batsman = first.split(" to ")
            return bowler.strip(), batsman.strip()
    except:
        pass
    return "Bowler", "Batsman"


# ---------------- BALL ---------------- #
def extract_ball(text):
    parts = text.split()
    if parts and "." in parts[0]:
        return parts[0]
    return ""


# ---------------- RUN BOT ---------------- #
def run_bot():
    global last_ball, over_data

    print("🔥 FULL PRO BOT RUNNING 🔥")

    while True:
        try:
            text, score_raw = fetch_data()

            if not text:
                print("No data...")
                time.sleep(10)
                continue

            ball = extract_ball(text)

            if ball and ball != last_ball:

                event, run = detect_event(text)
                over_data.append(run)

                bowler, batsman = extract_players(text)

                # SCORE PARSE
                try:
                    match = re.search(r"(\d+)\/(\d+)", score_raw)
                    overs = re.search(r"\((.*?)\)", score_raw)

                    runs = int(match.group(1))
                    wickets = int(match.group(2))
                    overs_val = float(overs.group(1))
                except:
                    runs, wickets, overs_val = 0, 0, 1

                # CRR
                crr = round(runs / overs_val, 2)

                # TARGET (JUGAAD)
                target = 200
                balls_left = int((20 - overs_val) * 6)
                runs_needed = target - runs

                if balls_left > 0:
                    rrr = round((runs_needed / balls_left) * 6, 2)
                else:
                    rrr = 0

                # ---------------- FINAL FORMAT ---------------- #
                msg = f"""
🏏 MATCH LIVE

📊 {runs}/{wickets} ({overs_val})
CRR: {crr}

🎯 {bowler} ➝ {batsman}
{event}

⏳ Balls Left: {balls_left}
⚡ Need {runs_needed} runs
RRR: {rrr}

📝 {text}
"""

                bot.send_message(CHANNEL_ID, msg)

                # OVER COMPLETE
                if ball.endswith(".6"):
                    over_msg = f"""
🔥 OVER COMPLETE
⚡ {' '.join(over_data)}
"""
                    bot.send_message(CHANNEL_ID, over_msg)
                    over_data = []

                last_ball = ball

            time.sleep(3)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)


if name == "__main__":
    run_bot()

import os
import time
import requests
import telebot

BOT_TOKEN = "8716019997:AAEYodES3bkjOXGxRXvC1D-wA65xqUM8jBk"
CHANNEL_ID = "@nextballLive"
API_KEY = "e3604d8c-b1eb-4d5f-b753-789a556d9bcb"

bot = telebot.TeleBot(BOT_TOKEN)

last_message = ""

def get_live_match():
    url = f"https://api.cricapi.com/v1/currentMatches?apikey={API_KEY}&offset=0"

    try:
        r = requests.get(url, timeout=15)
        data = r.json()
    except Exception as e:
        print("API request error:", e)
        return None

    if not data or data.get("status") != "success":
        print("API failed:", data)
        return None

    matches = data.get("data", [])
    if not matches:
        print("No matches found")
        return None

    # IPL / T20 / first live-looking match pick karne ki basic logic
    for match in matches:
        name = str(match.get("name", "")).lower()
        status = str(match.get("status", "")).lower()

        if "ipl" in name or "indian premier league" in name:
            return match

    # fallback: first current match
    return matches[0]

def format_score(match):
    team1 = match.get("teamInfo", [{}])[0].get("shortname", "TEAM1") if len(match.get("teamInfo", [])) > 0 else "TEAM1"
    team2 = match.get("teamInfo", [{}])[1].get("shortname", "TEAM2") if len(match.get("teamInfo", [])) > 1 else "TEAM2"

    score_list = match.get("score", [])
    status = match.get("status", "No status")

    score_lines = []
    for s in score_list:
        inning = s.get("inning", "")
        runs = s.get("r", "")
        wickets = s.get("w", "")
        overs = s.get("o", "")
        score_lines.append(f"{inning}: {runs}/{wickets} ({overs})")

    scores_text = "\n".join(score_lines) if score_lines else "Score loading..."

    msg = f"""🏏 {team1} vs {team2}

📊 {scores_text}

📝 {status}
"""
    return msg

def run_bot():
    global last_message

    print("🔥 CRICKETDATA BOT RUNNING 🔥")

    while True:
        try:
            match = get_live_match()

            if not match:
                print("No live match data")
                time.sleep(20)
                continue

            msg = format_score(match)

            if msg != last_message:
                bot.send_message(CHANNEL_ID, msg)
                print("Score update sent")
                last_message = msg
            else:
                print("No new update")

            time.sleep(20)

        except Exception as e:
            print("Error:", e)
            time.sleep(20)

if __name__ == "__main__":
    run_bot()

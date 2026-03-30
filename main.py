from pycricbuzz import Cricbuzz
import time
import telebot

BOT_TOKEN = "8716019997:AAEYodES3bkjOXGxRXvC1D-wA65xqUM8jBk"
CHANNEL_ID = "@nextballLive"

bot = telebot.TeleBot(BOT_TOKEN)

c = Cricbuzz()

last_ball = ""
over_data = []


def detect_event(text):
    t = text.lower()

    if "four" in t:
        return "🔥 FOUR!!!", "4"
    elif "six" in t:
        return "💣 SIX!!!", "6"
    elif "out" in t or "wicket" in t:
        return "💀 WICKET!!!", "W"
    elif "wide" in t:
        return "⚠️ WIDE", "Wd"
    elif "no ball" in t:
        return "🚫 NO BALL", "Nb"
    elif "1 run" in t:
        return "⚡ 1 RUN", "1"
    elif "2 runs" in t:
        return "⚡ 2 RUNS", "2"
    elif "3 runs" in t:
        return "⚡ 3 RUNS", "3"
    else:
        return "⚡ DOT BALL", "0"


def extract_players(text):
    try:
        parts = text.split(",")[0]
        if " to " in parts:
            bowler, batsman = parts.split(" to ")
            return bowler.strip(), batsman.strip()
    except:
        pass
    return "", ""


def run_bot():
    global last_ball, over_data

    print("🔥 VIP PRO BOT RUNNING 🔥")

    while True:
        try:
            matches = c.matches()
            if not matches:
                time.sleep(10)
                continue

            match = matches[0]
            match_id = match['id']
            team1 = match['team1']['name']
            team2 = match['team2']['name']

            score = c.livescore(match_id)

            try:
                runs = int(score['score'][0]['runs'])
                wickets = score['score'][0]['wickets']
                overs = float(score['score'][0]['overs'])
                score_text = f"{runs}/{wickets}"
            except:
                runs, overs = 0, 1
                score_text = "Loading..."
                overs = 1

            # CRR
            crr = round(runs / overs, 2)

            # Required runs (dummy target logic)
            target = 200  # change later dynamically
            runs_needed = target - runs
            balls_left = int((20 - overs) * 6)

            if balls_left > 0:
                rrr = round((runs_needed / balls_left) * 6, 2)
            else:
                rrr = 0

            comm = c.commentary(match_id)

            if not comm or "commentary" not in comm:
                time.sleep(10)
                continue

            latest = comm['commentary'][-1]

            ball = str(latest.get("over", ""))
            text = latest.get("comm", "")

            if ball and ball != last_ball:

                event, run = detect_event(text)
                over_data.append(run)

                bowler, batsman = extract_players(text)

                msg = f"""
🏏 {team1} vs {team2}

📊 {score_text} ({overs})
CRR: {crr}

🎯 {bowler} to {batsman}
{event}

⚡ Need {runs_needed} in {balls_left} balls
RRR: {rrr}

📝 {text}
"""

                bot.send_message(CHANNEL_ID, msg)

                if ball.endswith(".6"):
                    over_msg = f"""
🔥 OVER COMPLETE

⚡ This Over: {' '.join(over_data)}
"""
                    bot.send_message(CHANNEL_ID, over_msg)
                    over_data = []

                last_ball = ball

            time.sleep(5)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)


if __name__ == "__main__":
    run_bot()

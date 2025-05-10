from ollama import Client
import json
from datetime import datetime
import os

client = Client()

JOURNAL_FILE = "journal_storage.json"

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, "r") as f:
            return json.load(f)
    return []

def save_journal(data):
    with open(JOURNAL_FILE, "w") as f:
        json.dump(data, f, indent=2)




def analyze_mood(entry, journal_history):
    # tone hints to guide the model
    tone_hint = (
        "Possible tones include: happy, sad, excited, anxious, angry, content, neutral, lonely, tired, grateful.\n"
    )

    system_prompt = (
        "You are a gentle and emotionally intelligent mental health assistant. "
        "You help users reflect on their feelings and offer calming affirmations."
    )

    user_prompt = (
        f"{tone_hint}"
        f"Here is a journal entry:\n\"{entry}\"\n\n"
        "Respond ONLY in a humane way:\n"
        "mimic a psychiatrist:\n"
        "Tone: <one-word tone>\nAffirmation: <calming message>"
    )

    response = client.chat(
        model="phi",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )['message']['content']

    try:
        tone_line, affirmation_line = response.strip().split('\n', 1)
        tone = tone_line.split(":", 1)[1].strip().lower()
        affirmation = affirmation_line.split(":", 1)[1].strip()
    except Exception:
        tone = "neutral"
        
        fallback_prompt = (
            f"The user seems to be neutral right now. "
            f"Please suggest them some encouraging tips based on the journal entry:\n\"{entry}\""
        )
        affirmation = client.chat(
            model="phi",
            messages=[
                {"role": "system", "content": "You are a thoughtful companion providing emotionally supportive suggestions."},
                {"role": "user", "content": fallback_prompt}
            ]
        )['message']['content'].strip()
    bad_moods = {"sad", "anxious", "stressed", "angry", "lonely", "tired"}
    if tone in bad_moods and journal_history:
        comforting_entries = [
            log["entry"]
            for log in journal_history
            if log.get("tone") in {"happy", "content", "neutral", "grateful"}
        ]
        if comforting_entries:
            history_excerpt = "\n".join(f"- {e}" for e in comforting_entries[-5:])
            comfort_prompt = (
                f"The user is feeling {tone} right now.\n"
                f"Here are some of their past journal entries that made them feel better:\n"
                f"{history_excerpt}\n\n"
                f"Based on these and the current mood, suggest something that might help in a gentle and empathetic way."
            )

            extra_response = client.chat(
                model="phi",
                messages=[
                    {"role": "system", "content": "You are a thoughtful companion providing emotionally supportive suggestions."},
                    {"role": "user", "content": comfort_prompt}
                ]
            )['message']['content']

            affirmation += "\n\n🌱 Based on your past reflections:\n" + extra_response

    return tone, affirmation


def main():
    print("------Welcome to your Mental Health Journal Agent.------\n")
    journal_entry = input("Enter today's journal entry:📔\n> ")
    journal_data = load_journal()
    tone, affirmation = analyze_mood(journal_entry,journal_data)
    print(f"\n🎭 Detected Tone: {tone}")
    print(f"🪷 Affirmation: {affirmation}\n")
    log = {
        "timestamp": datetime.now().isoformat(),
        "entry": journal_entry,
        "tone" : tone,
        "affirmation":affirmation
    }

   
    journal_data.append(log)
    save_journal(journal_data)

    print("\n✅ Entry saved.")

if __name__ == "__main__":
    main()


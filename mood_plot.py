import json
import matplotlib.pyplot as plt
from datetime import datetime

# Assign numeric scores to moods
mood_scale = {
    "happy": 5,
    "content": 4,
    "neutral": 3,
    "anxious": 2,
    "stressed": 1,
    "sad": 0
}

def plot_mood_trend(filename="journal_storage.json"):
    with open(filename, "r") as f:
        data = json.load(f)

    dates = []
    moods = []

    for log in data:
        tone = log.get("tone", "neutral").lower()
        score = mood_scale.get(tone, 3)
        timestamp = datetime.fromisoformat(log["timestamp"])
        dates.append(timestamp)
        moods.append(score)

    if not dates:
        print("No data to plot.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(dates, moods, marker='o', linestyle='-', color='purple')
    plt.yticks(list(mood_scale.values()), list(mood_scale.keys()))
    plt.title("🧠 Mood Trend Over Time")
    plt.xlabel("Date")
    plt.ylabel("Mood Level")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_mood_trend()


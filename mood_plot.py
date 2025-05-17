
# mood_tools.py

import matplotlib
matplotlib.use("TkAgg")  # For headless or CLI use
import matplotlib.pyplot as plt
import json
import datetime

def generate_mood_plot(journal_path="journal.json", output_path="mood_plot.png"):
    moods = []
    timestamps = []

    with open(journal_path, "r") as f:
        for line in f:
            entry = json.loads(line)
            timestamps.append(datetime.datetime.fromisoformat(entry["timestamp"]))
            moods.append(entry["mood"].capitalize())

    # Convert moods to numeric values (simple encoding)
    mood_map = {m: i for i, m in enumerate(sorted(set(moods)))}
    mood_values = [mood_map[m] for m in moods]

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, mood_values, marker='o')
    plt.xticks(rotation=45)
    plt.yticks(list(mood_map.values()), list(mood_map.keys()))
    plt.title("Mood Over Time")
    plt.xlabel("Date")
    plt.ylabel("Mood")
    plt.tight_layout()
    plt.savefig(output_path)
    return output_path



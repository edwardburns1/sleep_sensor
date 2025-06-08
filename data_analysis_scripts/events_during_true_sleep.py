import os
import pandas as pd
import re
from datetime import datetime, timedelta


def count_events_between_true_sleep_and_wake(top_dir):
    skip_dates = {"2025-05-20", "2025-05-21", "2025-05-22"}
    event_counts = {}

    for entry in os.listdir(top_dir):
        if entry in skip_dates:
            continue

        dir_path = os.path.join(top_dir, entry)
        if not os.path.isdir(dir_path) or not re.match(r"\d{4}-\d{2}-\d{2}", entry):
            continue

        ground_truth_path = os.path.join(dir_path, "ground_truth_log.csv")
        journal_path = os.path.join(dir_path, "journal.txt")
        sleep_event_path = os.path.join(dir_path, "sleep_event_log.csv")

        if not (os.path.exists(ground_truth_path) and os.path.exists(journal_path) and os.path.exists(sleep_event_path)):
            continue

        try:
            # Read ground truth times
            gt_df = pd.read_csv(ground_truth_path, parse_dates=['timestamp'])
            if len(gt_df) < 2:
                continue
            bed_time = gt_df.iloc[0]['timestamp']
            wake_time = gt_df.iloc[1]['timestamp']

            # Read sleep onset latency
            with open(journal_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r"Sleep Onset Latency:\s*([\d.]+)", content)
            if not match:
                continue
            latency_minutes = float(match.group(1))

            # Calculate true sleep time
            true_sleep_time = bed_time #+ timedelta(minutes=latency_minutes)

            # Count events between true sleep and wake
            event_df = pd.read_csv(sleep_event_path, parse_dates=['timestamp'])
            if event_df.empty:
                continue

            mask = (event_df['timestamp'] >= true_sleep_time) & (event_df['timestamp'] <= wake_time)
            count = mask.sum()
            event_counts[datetime.strptime(entry, "%Y-%m-%d")] = count

        except Exception as e:
            print(f"Error processing {entry}: {e}")

    return dict(sorted(event_counts.items()))

import matplotlib.pyplot as plt

def plot_event_counts(event_counts, output_path="images/sleep_event_counts.png"):
    if not event_counts:
        print("No data to plot.")
        return

    dates = list(event_counts.keys())
    counts = list(event_counts.values())

    plt.figure(figsize=(10, 5))
    plt.plot(dates, counts, marker='o', linestyle='-', color='slateblue')
    plt.title("Sleep Events Between True Sleep Time and Wake Time")
    plt.xlabel("Date")
    plt.ylabel("Number of Events")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


top_directory = "sleep_data"
counts = count_events_between_true_sleep_and_wake(top_directory)

# Print counts
for date, count in counts.items():
    print(f"{date.date()}: {count} events")

# Plot them
plot_event_counts(counts)

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import re


def compute_event_wake_differences(top_dir):
    differences = {}  # {date: time_difference_in_minutes}

    for entry in os.listdir(top_dir):
        if entry == "2025-05-23":
            continue  # Skip this night

        dir_path = os.path.join(top_dir, entry)
        if not os.path.isdir(dir_path) or not re.match(r"\d{4}-\d{2}-\d{2}", entry):
            continue

        ground_truth_path = os.path.join(dir_path, "ground_truth_log.csv")
        sleep_event_path = os.path.join(dir_path, "sleep_event_log.csv")

        if not os.path.exists(ground_truth_path) or not os.path.exists(sleep_event_path):
            continue

        try:
            # Get wake time
            gt_df = pd.read_csv(ground_truth_path, parse_dates=['timestamp'])
            if len(gt_df) < 2:
                continue
            wake_time = gt_df.iloc[1]['timestamp']

            # Get closest event
            event_df = pd.read_csv(sleep_event_path, parse_dates=['timestamp'])
            if event_df.empty:
                continue

            event_df['time_diff'] = (event_df['timestamp'] - wake_time).abs()
            closest_event = event_df.loc[event_df['time_diff'].idxmin()]
            diff_minutes = abs((closest_event['timestamp'] - wake_time).total_seconds()) / 60.0

            differences[datetime.strptime(entry, "%Y-%m-%d")] = diff_minutes

        except Exception as e:
            print(f"Error processing {entry}: {e}")

    return dict(sorted(differences.items()))

def plot_event_wake_differences(differences, output_path="images/event_wake_differences.png"):
    if not differences:
        print("No differences to plot.")
        return

    dates = list(differences.keys())
    values = list(differences.values())

    # Print individual differences
    for date, diff in differences.items():
        print(f"{date.date()}: {diff:.2f} minutes")

    avg_diff = sum(values) / len(values)
    print(f"\nAverage difference: {avg_diff:.2f} minutes")

    # Plot
    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='o', linestyle='-', color='crimson')
    plt.title("Difference Between Wake Time and Nearest Sleep Event")
    plt.xlabel("Date")
    plt.ylabel("Difference (minutes)")
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(rotation=45)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

top_directory = "sleep_data"
diffs = compute_event_wake_differences(top_directory)
plot_event_wake_differences(diffs)

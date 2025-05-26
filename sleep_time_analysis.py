import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import re


def compute_event_sleep_differences(top_dir):
    differences = {}

    for entry in os.listdir(top_dir):
        if entry == "2025-05-23":
            continue  # Skip this night

        dir_path = os.path.join(top_dir, entry)
        if not os.path.isdir(dir_path) or not re.match(r"\d{4}-\d{2}-\d{2}", entry):
            continue

        ground_truth_path = os.path.join(dir_path, "ground_truth_log.csv")
        journal_path = os.path.join(dir_path, "journal.txt")
        sleep_event_path = os.path.join(dir_path, "sleep_event_log.csv")

        if not (os.path.exists(ground_truth_path) and os.path.exists(journal_path) and os.path.exists(sleep_event_path)):
            continue

        try:
            # 1. Get bed time
            gt_df = pd.read_csv(ground_truth_path, parse_dates=['timestamp'])
            if len(gt_df) < 1:
                continue
            bed_time = gt_df.iloc[0]['timestamp']

            # 2. Get latency from journal
            with open(journal_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r"Sleep Onset Latency:\s*([\d.]+)", content)
            if not match:
                continue
            latency_minutes = float(match.group(1))

            # 3. Compute real sleep time
            sleep_time = bed_time + timedelta(minutes=latency_minutes)

            # 4. Get nearest sleep event
            event_df = pd.read_csv(sleep_event_path, parse_dates=['timestamp'])
            if event_df.empty:
                continue
            event_df['time_diff'] = (event_df['timestamp'] - sleep_time).abs()
            closest_event = event_df.loc[event_df['time_diff'].idxmin()]
            diff_minutes = abs((closest_event['timestamp'] - sleep_time).total_seconds()) / 60.0

            differences[datetime.strptime(entry, "%Y-%m-%d")] = diff_minutes

        except Exception as e:
            print(f"Error processing {entry}: {e}")

    return dict(sorted(differences.items()))

def plot_event_sleep_differences(differences, output_path="images/event_sleep_differences.png"):
    if not differences:
        print("No sleep time differences to plot.")
        return

    dates = list(differences.keys())
    values = list(differences.values())

    for date, diff in differences.items():
        print(f"{date.date()}: {diff:.2f} minutes")

    avg_diff = sum(values) / len(values)
    print(f"\nAverage difference: {avg_diff:.2f} minutes")

    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='o', linestyle='-', color='darkgreen')
    plt.title("Difference Between Real Sleep Time and Nearest Sleep Event")
    plt.xlabel("Date")
    plt.ylabel("Difference (minutes)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

top_directory = "sleep_data"
sleep_diffs = compute_event_sleep_differences(top_directory)
plot_event_sleep_differences(sleep_diffs)

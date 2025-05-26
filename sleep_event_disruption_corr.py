import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import re
from scipy.stats import pearsonr


def compute_event_latency_correlation(top_dir):
    latencies = []
    event_counts = []

    skip_dates = {"2025-05-20", "2025-05-21", "2025-05-22", "2025-05-23"}

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
            # Read ground truth
            gt_df = pd.read_csv(ground_truth_path, parse_dates=['timestamp'])
            if len(gt_df) < 2:
                continue
            bed_time = gt_df.iloc[0]['timestamp']
            wake_time = gt_df.iloc[1]['timestamp']

            # Read latency
            with open(journal_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r"Sleep Onset Latency:\s*([\d.]+)", content)
            if not match:
                continue
            latency = float(match.group(1))

            # Count sleep events within bed-wake window
            event_df = pd.read_csv(sleep_event_path, parse_dates=['timestamp'])
            if event_df.empty:
                continue


            event_count = ((event_df['timestamp'] >= bed_time) & (event_df['timestamp'] <= wake_time)).sum()

            latencies.append(latency)
            event_counts.append(event_count)

        except Exception as e:
            print(f"Error processing {entry}: {e}")

    # Correlation calculation
    if len(latencies) > 1 and len(event_counts) > 1:
        r, p = pearsonr(event_counts, latencies)
        print(f"Pearson correlation (r): {r:.3f}")
        print(f"P-value: {p:.4f}")
    else:
        print("Not enough data to compute correlation.")

    # Plot for visual inspection
    plt.figure(figsize=(6, 5))
    plt.scatter(event_counts, latencies, color='steelblue')
    plt.title("Sleep Onset Latency vs. Sleep Event Count")
    plt.xlabel("Number of Sleep Events")
    plt.ylabel("Sleep Onset Latency (minutes)")
    plt.grid(True)
    plt.tight_layout()
    os.makedirs("images", exist_ok=True)
    plt.savefig("images/event_latency_correlation.png")
    plt.close()
    print("Saved: images/event_latency_correlation.png")

top_directory = "sleep_data"
compute_event_latency_correlation(top_directory)

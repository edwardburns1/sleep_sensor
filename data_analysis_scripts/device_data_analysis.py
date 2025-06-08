import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import re


def plot_sleep_events_for_all_nights(top_dir, output_dir="images/sleep_events"):
    os.makedirs(output_dir, exist_ok=True)

    for entry in os.listdir(top_dir):
        dir_path = os.path.join(top_dir, entry)
        if not os.path.isdir(dir_path) or not re.match(r"\d{4}-\d{2}-\d{2}", entry):
            continue

        ground_truth_path = os.path.join(dir_path, "ground_truth_log.csv")
        sleep_event_path = os.path.join(dir_path, "sleep_event_log.csv")

        if not os.path.exists(ground_truth_path) or not os.path.exists(sleep_event_path):
            print(f"Missing files in {entry}, skipping...")
            continue

        try:
            # Load sleep boundaries
            ground_truth = pd.read_csv(ground_truth_path, parse_dates=['timestamp'])
            if len(ground_truth) < 2:
                print(f"Invalid ground truth data in {entry}")
                continue
            bed_time = ground_truth.iloc[0]['timestamp']
            wake_time = ground_truth.iloc[1]['timestamp']
            start_time = bed_time - timedelta(hours=1)
            end_time = wake_time + timedelta(hours=1)

            # Load sleep events
            events = pd.read_csv(sleep_event_path, parse_dates=['timestamp'])
            filtered_events = events[(events['timestamp'] >= start_time) & (events['timestamp'] <= end_time)]

            # Plot
            plt.figure(figsize=(10, 4))
            for label in filtered_events['sleep_event'].unique():
                times = filtered_events[filtered_events['sleep_event'] == label]['timestamp']
                plt.scatter(times, [label] * len(times), label=label, s=30)

            plt.title(f"Sleep Events: {entry}")
            plt.xlabel("Time")
            plt.yticks(sorted(filtered_events['sleep_event'].unique()))
            plt.xlim(start_time, end_time)
            plt.grid(True, axis='x', linestyle='--', alpha=0.6)
            plt.tight_layout()
            plt.legend()

            output_path = os.path.join(output_dir, f"{entry}_events.png")
            plt.savefig(output_path)
            plt.close()
            print(f"Saved: {output_path}")

        except Exception as e:
            print(f"Error processing {entry}: {e}")
top_directory = "sleep_data"
plot_sleep_events_for_all_nights(top_directory)
import os
import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta
from scipy.stats import pearsonr


def extract_sensor_latency_averages(top_dir):
    latencies = []
    sensor_averages_by_night = {}  # date -> {sensor: avg}
    sensor_columns = ["temperature", "humidity", "heat_index", "light", "sound"]

    for entry in os.listdir(top_dir):
        dir_path = os.path.join(top_dir, entry)
        if not os.path.isdir(dir_path) or not re.match(r"\d{4}-\d{2}-\d{2}", entry):
            continue
        if entry == '2025-05-07':
            continue
        ground_truth_path = os.path.join(dir_path, "ground_truth_log.csv")
        journal_path = os.path.join(dir_path, "journal.txt")
        sensor_log_path = os.path.join(dir_path, "sensor_data_log.csv")

        if not (os.path.exists(ground_truth_path) and os.path.exists(journal_path) and os.path.exists(sensor_log_path)):
            continue

        try:
            # Get bed time
            gt_df = pd.read_csv(ground_truth_path, parse_dates=['timestamp'])
            if len(gt_df) < 1:
                continue
            bed_time = gt_df.iloc[0]['timestamp']

            # Get latency
            with open(journal_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r"Sleep Onset Latency:\s*([\d.]+)", content)
            if not match:
                continue
            latency = float(match.group(1))
            latencies.append(latency)

            # Time window
            start_time = bed_time
            end_time = bed_time + timedelta(minutes=latency)

            # Get sensor data
            sensor_df = pd.read_csv(sensor_log_path, parse_dates=['timestamp'])
            interval_data = sensor_df[(sensor_df['timestamp'] >= start_time) & (sensor_df['timestamp'] <= end_time)]

            if interval_data.empty:
                # Fallback: use nearest datapoint to sleep onset time
                target_time = bed_time + timedelta(minutes=latency)
                sensor_df['abs_diff'] = (sensor_df['timestamp'] - target_time).abs()
                nearest_row = sensor_df.loc[sensor_df['abs_diff'].idxmin()]
                avg_dict = {sensor: nearest_row[sensor] for sensor in sensor_columns}
            else:
                avg_dict = {sensor: interval_data[sensor].mean() for sensor in sensor_columns}


            avg_dict = {sensor: interval_data[sensor].mean() for sensor in sensor_columns}
            sensor_averages_by_night[datetime.strptime(entry, "%Y-%m-%d")] = avg_dict

        except Exception as e:
            print(f"Error processing {entry}: {e}")

    return latencies, sensor_averages_by_night


def plot_sensor_averages_and_correlate(latencies, sensor_averages_by_night, output_dir="images/sensor_latency"):
    os.makedirs(output_dir, exist_ok=True)

    if not sensor_averages_by_night:
        print("No sensor data to process.")
        return

    dates = sorted(sensor_averages_by_night.keys())
    sensors = list(next(iter(sensor_averages_by_night.values())).keys())

    # Reconstruct per-sensor time series
    for sensor in sensors:
        values = [sensor_averages_by_night[date][sensor] for date in dates]
        plt.figure(figsize=(10, 5))
        plt.plot(dates, values, marker='o', linestyle='-', label=sensor, color='mediumseagreen')
        plt.title(f"Average {sensor.capitalize()} During Sleep Onset Interval")
        plt.xlabel("Date")
        plt.ylabel(sensor.capitalize())
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{sensor}_averages.png")
        plt.close()
        print(f"Saved: {output_dir}/{sensor}_averages.png")

        # Correlation
        r, p = pearsonr(values, latencies)
        print(f"{sensor.capitalize()} correlation with sleep latency:")
        print(f"  Pearson r = {r:.3f}, p = {p:.4f}\n")

top_directory = "sleep_data"
latencies, sensor_data = extract_sensor_latency_averages(top_directory)
plot_sensor_averages_and_correlate(latencies, sensor_data)

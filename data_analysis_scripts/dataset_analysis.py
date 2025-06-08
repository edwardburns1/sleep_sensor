import os
import re
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter


def extract_sleep_data_and_keyword_counts(top_dir):
    latency_by_date = {}
    quality_by_date = {}
    keyword_counts = {
        "melatonin": Counter(),
        "unisom": Counter()
    }

    for entry in os.listdir(top_dir):
        dir_path = os.path.join(top_dir, entry)
        if os.path.isdir(dir_path) and re.match(r"\d{4}-\d{2}-\d{2}", entry):
            journal_path = os.path.join(dir_path, "journal.txt")
            if os.path.exists(journal_path):
                try:
                    with open(journal_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content_lower = content.lower()
                    date = datetime.strptime(entry, "%Y-%m-%d")

                    # Extract latency and quality
                    latency_match = re.search(r"Sleep Onset Latency:\s*([\d.]+)", content)
                    if latency_match:
                        latency_by_date[date] = float(latency_match.group(1))

                    quality_match = re.search(r"Sleep Quality:\s*([\d.]+)", content)
                    if quality_match:
                        quality_by_date[date] = float(quality_match.group(1))

                    # Count keyword mentions
                    for keyword in keyword_counts:
                        if keyword in content_lower:
                            keyword_counts[keyword]["mentioned"] += 1
                        else:
                            keyword_counts[keyword]["not_mentioned"] += 1

                except Exception as e:
                    print(f"Error reading {journal_path}: {e}")

    return (
        dict(sorted(latency_by_date.items())),
        dict(sorted(quality_by_date.items())),
        keyword_counts
    )



def plot_time_series(data, title, ylabel, output_path):
    if not data:
        print(f"No {ylabel} data to plot.")
        return

    dates = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='o', linestyle='-', color='teal')
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(rotation=45)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def categorize_latency(latency_data):
    categories = {
        "Normal": 0,
        "Mild Insomnia": 0,
        "Severe Insomnia": 0
    }

    for latency in latency_data.values():
        if latency <= 30:
            categories["Normal"] += 1
        elif latency <= 90:
            categories["Mild Insomnia"] += 1
        else:
            categories["Severe Insomnia"] += 1

    return categories


def plot_latency_categories(categories, output_path):
    labels = list(categories.keys())
    values = list(categories.values())
    colors = ['green', 'gold', 'red']  # green for Normal, yellow for Mild, red for Severe

    plt.figure(figsize=(6, 5))
    plt.bar(labels, values, color=colors)
    plt.title("Sleep Onset Latency Categorization")
    plt.ylabel("Number of Nights")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")



def plot_keyword_counts(keyword, counts, output_path):
    labels = ['Consumed', 'Not Consumed']
    values = [counts['mentioned'], counts['not_mentioned']]

    plt.figure(figsize=(6, 5))
    plt.bar(labels, values, color='slateblue')
    plt.title(f"'{keyword.capitalize()}' Consumption")
    plt.ylabel("Number of Nights")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


# Example usage
top_directory = "sleep_data"
latency_data, quality_data, keyword_counts = extract_sleep_data_and_keyword_counts(top_directory)

plot_time_series(latency_data, "Sleep Onset Latency Over Time", "Sleep Onset Latency (minutes)",
                 "../images/sleep_latency.png")

plot_time_series(quality_data, "Sleep Quality Over Time", "Sleep Quality (1–5 scale)", "../images/sleep_quality.png")

# Categorize and plot sleep onset latency
latency_categories = categorize_latency(latency_data)
plot_latency_categories(latency_categories, "../images/latency_categories.png")

# Plot keyword mentions
for keyword, counts in keyword_counts.items():
    output_file = f"images/{keyword}_mentions.png"
    plot_keyword_counts(keyword, counts, output_file)

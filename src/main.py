import schedule
import os
import json
from datetime import datetime, timedelta
from elpriser.fetcher import Fetcher
from elpriser.categorizer import Categorizer
from elpriser.lookahead import Lookahead
from flask import Flask, jsonify

app = Flask("ElpriserDK")

def fetch_next_day_prices():
    fetcher = Fetcher()
    tomorrow = datetime.now() + timedelta(days=1)
    fetcher.fetch_prices(date=tomorrow)
    print(f"Fetched prices for {tomorrow.strftime('%Y-%m-%d')}")

def get_additional_cost(dt):
    hour = dt.hour
    if 0 <= hour < 6:
        return 1.19
    elif 6 <= hour < 17:
        return 1.25
    elif 17 <= hour < 21:
        return 1.54
    else:
        return 1.25

def get_prices_from_local_files():
    responses_dir = os.path.join(os.path.dirname(__file__), 'elpriser', 'responses')
    today = datetime.now()
    prices = {}
    # Load last 7 days
    for i in range(7):
        day = today - timedelta(days=i)
        filename = f"{day.year}-{day.month:02d}-{day.day:02d}.json"
        filepath = os.path.join(responses_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                try:
                    day_prices = json.load(f)
                    for entry in day_prices:
                        dt = datetime.fromisoformat(entry['time_start'].replace('Z', '+00:00'))
                        total_cost = entry['DKK_per_kWh'] + get_additional_cost(dt)
                        prices[entry['time_start']] = total_cost
                except Exception:
                    continue
    return prices

# Helper to get today's prices

def get_today_prices():
    responses_dir = os.path.join(os.path.dirname(__file__), 'elpriser', 'responses')
    today = datetime.now()
    filename = f"{today.year}-{today.month:02d}-{today.day:02d}.json"
    filepath = os.path.join(responses_dir, filename)
    prices = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            day_prices = json.load(f)
            for entry in day_prices:
                dt = datetime.fromisoformat(entry['time_start'].replace('Z', '+00:00'))
                total_cost = entry['DKK_per_kWh'] + get_additional_cost(dt)
                prices[entry['time_start']] = total_cost
    return prices

@app.route('/lookahead')
def lookahead_endpoint():
    prices = get_today_prices()
    lookahead = Lookahead()
    cumulative_price, lookahead_window = lookahead.get_lookahead_window(prices, window=6, from_now=True)
    categorizer = Categorizer()
    hourly_thresholds = categorizer.total_thresholds
    amber_threshold = hourly_thresholds["amber"] * 6
    red_threshold = hourly_thresholds["red"] * 6
    if cumulative_price < amber_threshold:
        category = "green"
    elif amber_threshold <= cumulative_price < red_threshold:
        category = "amber"
    else:
        category = "red"
    if not lookahead_window:
        return jsonify({
            "error": "No data available for the next 6 hours",
            "time_window": [],
            "cumulative_cost": None,
            "category": None
        }), 404
    return jsonify({
        "time_window": [lookahead_window[0], lookahead_window[-1]],
        "cumulative_cost": cumulative_price,
        "category": category
    })

@app.route('/today')
def today_endpoint():
    prices = get_today_prices()
    categorizer = Categorizer()
    hourly = []
    for time, cost in prices.items():
        hourly.append({
            "time": time,
            "cost": cost,
            "category": categorizer.categorize(cost)
        })
    return jsonify(hourly)

@app.route('/tomorrow')
def tomorrow_endpoint():
    # Fetch tomorrow's prices from API
    tomorrow = datetime.now() + timedelta(days=1)
    year = tomorrow.year
    month = f"{tomorrow.month:02d}"
    day = f"{tomorrow.day:02d}"
    region = "DK2"
    url = f"https://www.elprisenligenu.dk/api/v1/prices/{year}/{month}-{day}_{region}.json"
    responses_dir = os.path.join(os.path.dirname(__file__), 'elpriser', 'responses')
    filename = f"{year}-{month}-{day}.json"
    filepath = os.path.join(responses_dir, filename)
    try:
        import requests
        response = requests.get(url)
        if response.status_code == 200:
            day_prices = response.json()
            # Save to local file for future use
            with open(filepath, 'w') as f:
                json.dump(day_prices, f)
            prices = {}
            for entry in day_prices:
                dt = datetime.fromisoformat(entry['time_start'].replace('Z', '+00:00'))
                total_cost = entry['DKK_per_kWh'] + get_additional_cost(dt)
                prices[entry['time_start']] = total_cost
            hourly = []
            categorizer = Categorizer()
            for time, cost in prices.items():
                hourly.append({
                    "time": time,
                    "cost": cost,
                    "category": categorizer.categorize(cost)
                })
            return jsonify(hourly)
        else:
            return jsonify({"error": "No data available for tomorrow"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def ensure_last_7_days_data():
    responses_dir = os.path.join(os.path.dirname(__file__), 'elpriser', 'responses')
    if not os.path.exists(responses_dir):
        os.makedirs(responses_dir)
    today = datetime.now()
    # Generate the set of filenames for the last 7 days
    last_7_days = set()
    for i in range(7):
        day = today - timedelta(days=i)
        filename = f"{day.year}-{day.month:02d}-{day.day:02d}.json"
        last_7_days.add(filename)
        filepath = os.path.join(responses_dir, filename)
        if not os.path.exists(filepath):
            fetcher = Fetcher()
            day_prices = fetcher.fetch_prices(date=day)
            if day_prices:
                with open(filepath, 'w') as f:
                    json.dump(day_prices, f)
                print(f"Fetched and saved prices for {day.strftime('%Y-%m-%d')}")
            else:
                print(f"Fetched prices for {day.strftime('%Y-%m-%d')}, but no data to save.")
    # Delete files older than last 7 days
    for fname in os.listdir(responses_dir):
        if fname.endswith('.json') and fname not in last_7_days:
            os.remove(os.path.join(responses_dir, fname))
            print(f"Deleted old price file: {fname}")

def list_response_files():
    responses_dir = os.path.join(os.path.dirname(__file__), 'elpriser', 'responses')
    files = [f for f in os.listdir(responses_dir)
             if os.path.isfile(os.path.join(responses_dir, f)) and f != '.gitkeep']
    return sorted(files)

@app.route('/responses')
def responses_endpoint():
    files = list_response_files()
    return jsonify({"files": files})

def main():
    categorizer = Categorizer()
    lookahead = Lookahead()

    prices = get_prices_from_local_files()

    # Single six-hour look-ahead from this moment
    cumulative_price, lookahead_window = lookahead.get_lookahead_window(prices, window=6, from_now=True)
    # Re-categorize cumulative_price based on hourly threshold times 6
    hourly_thresholds = categorizer.total_thresholds
    amber_threshold = hourly_thresholds["amber"] * 6
    red_threshold = hourly_thresholds["red"] * 6
    if cumulative_price < amber_threshold:
        lookahead_category = "green"
    elif amber_threshold <= cumulative_price < red_threshold:
        lookahead_category = "amber"
    else:
        lookahead_category = "red"
    print("\nSix-Hour Look-Ahead (from now):")
    print(f"Time window: {lookahead_window[0]} to {lookahead_window[-1]}")
    print(f"Cumulative cost for a 1 KW device for 6 hours: {cumulative_price}")
    print(f"Category: {lookahead_category}")

if __name__ == "__main__":
    ensure_last_7_days_data()
    # Schedule checking next day's prices every hour
    schedule.every().hour.do(fetch_next_day_prices)
    main()
    app.run(host="0.0.0.0", port=5000)
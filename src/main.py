import schedule
import time
import os
import json
from datetime import datetime, timedelta
from elpriser.fetcher import Fetcher
from elpriser.categorizer import Categorizer
from elpriser.lookahead import Lookahead
from flask import Flask, jsonify

app = Flask(__name__)

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
    cumulative_price, category, lookahead_window = lookahead.get_lookahead_window(prices, window=6, from_now=True)
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

@app.route('/hourly')
def hourly_endpoint():
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

def main():
    categorizer = Categorizer()
    lookahead = Lookahead()

    prices = get_prices_from_local_files()

    # Categorize current prices
    categorized_prices = {time: categorizer.categorize(price) for time, price in prices.items()}

    # Single six-hour look-ahead from this moment
    cumulative_price, category, lookahead_window = lookahead.get_lookahead_window(prices, window=6, from_now=True)
    print("\nSix-Hour Look-Ahead (from now):")
    print(f"Time window: {lookahead_window[0]} to {lookahead_window[-1]}")
    print(f"Cumulative cost: {cumulative_price}")
    print(f"Category: {category}")

if __name__ == "__main__":
    # Schedule fetching next day's prices at 15:00 every day
    schedule.every().day.at("15:00").do(fetch_next_day_prices)
    main()
    # Only run the scheduler if explicitly requested
    # Comment out the infinite loop to allow normal exit
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
    app.run(host="0.0.0.0", port=5000)
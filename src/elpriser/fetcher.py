import os
import json
from datetime import datetime, timedelta
import requests

class Fetcher:
    def __init__(self):
        self.base_url = "https://www.elprisenligenu.dk/api/v1/prices/"
        self.data_dir = os.path.join(os.path.dirname(__file__), 'responses')

    def fetch_prices(self, date=None):
        if date is None:
            today = datetime.now()
        else:
            today = date
        year = today.year
        month = f"{today.month:02d}"
        day = f"{today.day:02d}"
        region = "DK2"
        final_url = f"{self.base_url}{year}/{month}-{day}_{region}.json"
        response = requests.get(final_url, timeout=10)
        if response.status_code == 200:
            prices = response.json()
            # Save to file
            filename = f"{year}-{month}-{day}.json"
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            with open(filepath, 'w') as f:
                json.dump(prices, f)
            print(f"Fetched prices for {year}-{month}-{day} and saved to {filepath}")
            return prices
        else:
            print(response.status_code)
            raise Exception("Failed to fetch prices from elpriser.dk")

    def load_last_7_days(self):
        today = datetime.now()
        days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        all_prices = []
        for day in days:
            filename = f"{day}.json"
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    all_prices.append(json.load(f))
        return all_prices
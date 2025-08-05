from datetime import datetime, timedelta
import os
import json

class Lookahead:
    def __init__(self):
        pass

    def get_lookahead_window(self, prices, window=6, from_now=True):
        times = sorted(prices.keys())
        # If from_now, start from the current hour
        if from_now:
            now = datetime.now().replace(minute=0, second=0, microsecond=0)
            start_idx = next((i for i, t in enumerate(times) if t >= now.isoformat()), 0)
        else:
            start_idx = 0
        lookahead = times[start_idx:start_idx+window]
        # If lookahead is shorter than window, try to load next day's prices
        if len(lookahead) < window:
            # Get next day
            last_time = datetime.fromisoformat(times[-1].replace('Z', '+00:00'))
            next_day = last_time + timedelta(days=1)
            next_filename = f"{next_day.year}-{next_day.month:02d}-{next_day.day:02d}.json"
            responses_dir = os.path.join(os.path.dirname(__file__), 'responses')
            next_filepath = os.path.join(responses_dir, next_filename)
            if os.path.exists(next_filepath):
                with open(next_filepath, 'r') as f:
                    next_prices = json.load(f)
                next_times = [entry['time_start'] for entry in next_prices]
                # Add next day's times to lookahead
                for t in next_times:
                    if len(lookahead) >= window:
                        break
                    lookahead.append(t)
                # Add next day's prices to prices dict
                for entry in next_prices:
                    prices[entry['time_start']] = entry['DKK_per_kWh']
        cumulative_price = sum(prices[t] for t in lookahead)
        # Only return cumulative_price and lookahead; let caller handle categorization
        return cumulative_price, lookahead
from datetime import datetime

class Lookahead:
    def __init__(self):
        pass

    def get_lookahead_window(self, prices, window=6, from_now=True):
        times = sorted(prices.keys())
        # If from_now, start from the current hour
        if from_now:
            now = datetime.now().replace(minute=0, second=0, microsecond=0)
            # Find the first time >= now
            start_idx = next((i for i, t in enumerate(times) if t >= now.isoformat()), 0)
        else:
            start_idx = 0
        lookahead = times[start_idx:start_idx+window]
        cumulative_price = sum(prices[t] for t in lookahead)
        category = self.categorize(cumulative_price)
        return cumulative_price, category, lookahead

    def categorize(self, cumulative_price):
        if cumulative_price < 3.0:
            return "green"
        elif 3.0 <= cumulative_price < 6.0:
            return "amber"
        else:
            return "red"
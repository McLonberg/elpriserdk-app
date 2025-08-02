# Thresholds
RED_THRESHOLD = 2.5
AMBER_THRESHOLD = 1.5


class Categorizer:
    def __init__(self, raw_thresholds=None, total_thresholds=None):
        # Thresholds for raw price (excluding additional costs)
        self.raw_thresholds = raw_thresholds or {
            "green": 0.0,
            "amber": 0.6,
            "red": 1.0
        }
        # Thresholds for total price (including additional costs)
        self.total_thresholds = total_thresholds or {
            "green": 0.0,
            "amber": 1.5,
            "red": 2.5
        }

    def categorize(self, price, use_total=True):
        """
        Categorize price using either raw or total thresholds.
        :param price: The price value to categorize
        :param use_total: If True, use total thresholds (including additional costs). If False, use raw thresholds.
        """
        thresholds = self.total_thresholds if use_total else self.raw_thresholds
        if price < thresholds["amber"]:
            return "green"
        elif thresholds["amber"] <= price < thresholds["red"]:
            return "amber"
        else:
            return "red"
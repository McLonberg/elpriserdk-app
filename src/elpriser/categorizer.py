# Thresholds
RED_THRESHOLD = 2.5
AMBER_THRESHOLD = 1.5


class Categorizer:
    def __init__(self, red_threshold=RED_THRESHOLD, amber_threshold=AMBER_THRESHOLD):
        self.red_threshold = red_threshold
        self.amber_threshold = amber_threshold

    def categorize(self, price):
        if price >= self.red_threshold:
            return "red"
        elif price >= self.amber_threshold:
            return "amber"
        else:
            return "green"
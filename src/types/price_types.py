from enum import Enum

class PriceCategory(Enum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"

class PriceData:
    def __init__(self, hour: str, price: float, category: PriceCategory):
        self.hour = hour
        self.price = price
        self.category = category

    def __repr__(self):
        return f"PriceData(hour={self.hour}, price={self.price}, category={self.category})"
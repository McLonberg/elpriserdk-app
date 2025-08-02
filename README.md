# Electricity Price Lookup Application

This application retrieves electricity prices from elpriser.dk, categorizes them into red, amber, or green based on predefined thresholds, and implements a six-hour look-ahead feature.

## Project Structure

```
elpriserdk-app
├── src
│   ├── main.py               # Entry point of the application
│   ├── elpriser
│   │   ├── fetcher.py        # Fetches electricity prices
│   │   ├── categorizer.py     # Categorizes prices
│   │   └── lookahead.py       # Implements six-hour look-ahead feature
│   └── types
│       └── price_types.py     # Defines data types and constants
├── requirements.txt           # Lists project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd elpriserdk-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python src/main.py
```

This will initialize the application, fetch the current electricity prices, categorize them, and display the four-hour look-ahead prices with their respective categories.

## Categories

- **Red**: High electricity prices
- **Amber**: Moderate electricity prices
- **Green**: Low electricity prices

Adjust the thresholds in `src/elpriser/categorizer.py` to modify the categorization logic as needed.

## API Routes

The application exposes the following API endpoints:

- `GET /lookahead`
  - Returns the six-hour look-ahead cumulative price and its category for the current day.

- `GET /today`
  - Returns a list of today's hourly electricity prices, each with its time, cost, and category.

- `GET /tomorrow`
  - Returns tomorrow's hourly electricity prices and their categories (if available).

- `GET /responses`
  - Returns a sorted list of all files in the responses folder (excluding .gitkeep).

Each endpoint returns data in JSON format. See the source code in `src/main.py` for implementation details.
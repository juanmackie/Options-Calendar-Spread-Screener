Here's the content formatted as Markdown:

```markdown
# Calendar Spread Screener Overview

This Python script is designed to scan the US options market for potentially profitable weekly calendar spread opportunities. It leverages real-time market data from the Polygon.io API to identify trades that fit a specific set of criteria.

The core goal of the script is to find **At-The-Money (ATM) calendar spreads (calls, puts, or both)** where the trader receives a net credit. This strategy aims to profit from the accelerated time decay (theta) of the short-term option relative to the long-term option, and potentially from changes in implied volatility.

## Features

- **Automated Scanning**: Scans a predefined list of stocks and ETFs for opportunities.
- **Configurable Contract Types**: Can scan for call spreads, put spreads, or both.
- **Dynamic Expiry Dates**: Automatically calculates the next two weekly (Friday) expiration dates to construct the spreads.
- **ATM Strike Identification**: Fetches the current stock price to find the closest At-The-Money strike price for the selected contract type(s).
- **Intelligent Filtering**: Applies a multi-point check to each potential spread:
  - **Liquidity Check**: Ensures options have sufficient volume and open interest.
  - **Net Credit**: Filters for spreads that provide a minimum upfront credit.
  - **Implied Volatility (IV) Differential**: Seeks a higher IV in the near-term option compared to the far-term, by a configurable margin.
  - **Positive Theta**: Optionally ensures the overall position has positive time decay.
- **Clear Output**: Presents the results in a clean, readable table format using pandas, sorted by net credit.

## Requirements

- Python 3.6+
- `requests` library
- `pandas` library
- A Polygon.io API Key (a free key is sufficient for this script)

## Setup & Configuration

### Install Libraries

If you don't have them installed, open your terminal or command prompt and run:

```bash
pip install pandas requests
```

### Get a Polygon.io API Key

1. Go to the [Polygon.io](https://polygon.io/) website and sign up for a free account.
2. Navigate to your dashboard to find your API key.

### Configure the API Key

Open the `screener.py` file.

Find the line:

```python
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'YOUR_API_KEY_HERE')
```

**Option A (Recommended for security)**:
Set the API key as an environment variable named `POLYGON_API_KEY`.

**Option B (Simpler)**:
Replace `'YOUR_API_KEY_HERE'` with your actual Polygon.io API key. For example:

```python
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'AbcDeFg12345')
```

## How to Run

Once the setup is complete, you can run the screener from your terminal:

```bash
python screener.py
```

The script will print its progress as it scans each ticker and will display a final table of any opportunities that match the criteria.

## Customization

You can easily tailor the screener to your preferences by modifying the **SCREENING PARAMETERS** section at the top of the `screener.py` script.

### Core Parameters:
- `STOCKS_TO_SCAN`: A list of stock or ETF tickers to scan.
  - Example: `STOCKS_TO_SCAN = ['MSFT', 'GOOGL', 'AMZN', 'SPY']`
- `CONTRACT_TYPE_TO_SCAN`: Determines the type of options to scan.
  - `'call'`: Scans for call calendar spreads.
  - `'put'`: Scans for put calendar spreads.
  - `'both'`: Scans for both call and put calendar spreads.
  - Example: `CONTRACT_TYPE_TO_SCAN = 'call'`

### Filtering Criteria:
- `MIN_OPTION_VOLUME`: Minimum daily trading volume for each option leg.
  - Example: `MIN_OPTION_VOLUME = 100`
- `MIN_OPTION_OPEN_INTEREST`: Minimum open interest for each option leg.
  - Example: `MIN_OPTION_OPEN_INTEREST = 500`
- `MIN_NET_CREDIT`: Minimum net credit required for the spread (e.g., 0.01 for at least $1 credit per share).
  - Example: `MIN_NET_CREDIT = 0.01`
- `MIN_IV_PREMIUM_NEAR_OVER_FAR`: Minimum difference by which the near-term option's Implied Volatility (IV) must exceed the far-term option's IV. A positive value means the near-term IV must be higher.
  - Example: `MIN_IV_PREMIUM_NEAR_OVER_FAR = 0.0` (Near IV must be >= Far IV)
  - Example: `MIN_IV_PREMIUM_NEAR_OVER_FAR = 0.05` (Near IV must be at least 5% higher than Far IV)
- `REQUIRE_POSITIVE_NET_THETA`: Boolean. If `True`, the spread must have a net positive theta (time decay works in your favor).
  - Example: `REQUIRE_POSITIVE_NET_THETA = True`

### Example Configuration Block:
```python
# --- SCREENING PARAMETERS ---
STOCKS_TO_SCAN = ['AAPL', 'TSLA', 'NVDA', 'QQQ', 'SPY', 'AMD']
CONTRACT_TYPE_TO_SCAN = 'call' # Options: 'call', 'put', 'both'

MIN_OPTION_VOLUME = 50
MIN_OPTION_OPEN_INTEREST = 200
MIN_NET_CREDIT = 0.05 # Require at least $0.05 credit
MIN_IV_PREMIUM_NEAR_OVER_FAR = 0.02 # Near IV should be at least 2% > Far IV
REQUIRE_POSITIVE_NET_THETA = True
```

## Disclaimer

This script is for **educational and informational purposes only**. It is **not financial advice**. Options trading is inherently risky and can result in significant financial loss. The data provided by the API may have delays or inaccuracies. Always conduct your own research and consult with a qualified financial advisor before making any investment decisions.
```

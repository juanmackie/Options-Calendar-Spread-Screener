Here's the content formatted as Markdown:

```markdown
# Calendar Spread Screener Overview

This Python script is designed to scan the US options market for potentially profitable weekly calendar spread opportunities. It leverages real-time market data from the Polygon.io API to identify trades that fit a specific set of criteria based on established options trading principles for this strategy.

The core goal of the script is to find **At-The-Money (ATM) call calendar spreads** where the trader receives a net credit. This strategy aims to profit from the accelerated time decay (theta) of the short-term option relative to the long-term option.

## Features

- **Automated Scanning**: Scans a predefined list of stocks and ETFs for opportunities.
- **Dynamic Expiry Dates**: Automatically calculates the next two weekly (Friday) expiration dates to construct the spreads.
- **ATM Strike Identification**: Fetches the current stock price to find the closest At-The-Money strike price.
- **Intelligent Filtering**: Applies a multi-point check to each potential spread:
  - **Liquidity Check**: Ensures options have sufficient volume and open interest to be easily tradable.
  - **Net Credit**: Filters for spreads that provide an upfront credit to the trader.
  - **Implied Volatility (IV) Differential**: Looks for situations where the near-term option has a higher IV than the far-term option, which is ideal for this strategy.
  - **Positive Theta**: Confirms that the overall position has positive time decay, meaning the position should profit as time passes, all else being equal.
- **Clear Output**: Presents the results in a clean, readable table format using pandas.

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

Open the `options_screener_script.py` file.

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
python options_screener_script.py
```

The script will print its progress as it scans each ticker and will display a final table of any opportunities that match the criteria.

## Customization

You can easily tailor the screener to your preferences by modifying the **SCREENING PARAMETERS** section at the top of the script.

### Example Customizations

```python
STOCKS_TO_SCAN = ['MSFT', 'GOOGL', 'AMZN', 'IWM']  # Change the list of stock tickers to scan
MIN_VOLUME = 100  # Adjust the minimum required daily trading volume for an option contract
MIN_OPEN_INTEREST = 50  # Adjust the minimum required open interest for an option contract
```

## Disclaimer

This script is for **educational and informational purposes only**. It is **not financial advice**. Options trading is inherently risky and can result in significant financial loss. The data provided by the API may have delays or inaccuracies. Always conduct your own research and consult with a qualified financial advisor before making any investment decisions.
```

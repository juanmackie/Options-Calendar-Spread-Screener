import os
import requests
import pandas as pd
from datetime import date, timedelta

# --- CONFIGURATION ---
# IMPORTANT: Add your Polygon.io API key here. You can get a free key from their website.
# It's recommended to set this as an environment variable for security.
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'YOUR_API_KEY_HERE')

# --- SCREENING PARAMETERS ---
# This list would ideally be dynamic, based on insights from X or other sentiment analysis.
# For this script, we'll use a static list of commonly traded, volatile stocks.
STOCKS_TO_SCAN = ['AAPL', 'TSLA', 'NVDA', 'QQQ', 'SPY', 'AMD']

# Define minimum liquidity thresholds to avoid options that are hard to trade.
MIN_VOLUME = 100
MIN_OPEN_INTEREST = 500

# --- HELPER FUNCTIONS ---

def get_next_fridays(n=2):
    """
    Calculates the next 'n' Fridays from today, which are typical weekly option expiration dates.
    """
    fridays = []
    today = date.today()
    # Start with today and find the first upcoming Friday
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0 and today.weekday() == 4: # If today is Friday
        current_friday = today
    else:
        current_friday = today + timedelta(days=days_ahead)

    for i in range(n):
        fridays.append(current_friday + timedelta(weeks=i))
    return [d.strftime('%Y-%m-%d') for d in fridays]

def get_stock_price(ticker: str) -> float:
    """
    Fetches the last traded price for a given stock ticker using the Polygon API.
    """
    url = f"https://api.polygon.io/v2/last/trade/{ticker}?apiKey={POLYGON_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('results'):
            return data['results']['p']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stock price for {ticker}: {e}")
    return 0.0

def find_atm_options_for_spread(ticker: str, near_expiry: str, far_expiry: str):
    """
    Finds potential At-The-Money (ATM) calendar spreads for a given stock.

    This function fetches the full option chain for a ticker, identifies the ATM strike,
    and then finds the corresponding call options for the near and far expiries.
    """
    print(f"\nScanning {ticker} for spreads between {near_expiry} and {far_expiry}...")

    # 1. Get current stock price to determine the ATM strike
    current_price = get_stock_price(ticker)
    if not current_price:
        print(f"Could not get current price for {ticker}. Skipping.")
        return None

    print(f"Current {ticker} price: ${current_price:.2f}")

    # 2. Fetch the entire options snapshot for the ticker
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/options/tickers/{ticker}?apiKey={POLYGON_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching options snapshot for {ticker}: {e}")
        return None

    if not data.get('tickers'):
        print(f"No options data found for {ticker}.")
        return None

    # 3. Find the ATM strike price
    all_strikes = sorted(list(set(option['details']['strike_price'] for option in data['tickers'])))
    if not all_strikes:
        print(f"No strikes found for {ticker}.")
        return None
        
    atm_strike = min(all_strikes, key=lambda x: abs(x - current_price))
    print(f"Identified At-The-Money (ATM) strike: ${atm_strike}")

    # 4. Find the near-term and far-term options at the ATM strike
    near_term_option = None
    far_term_option = None

    for option in data['tickers']:
        details = option.get('details', {})
        if details.get('strike_price') == atm_strike and details.get('contract_type', '').lower() == 'call':
            if details.get('expiration_date') == near_expiry:
                near_term_option = option
            elif details.get('expiration_date') == far_expiry:
                far_term_option = option
        # Stop searching if both are found
        if near_term_option and far_term_option:
            break
            
    if not near_term_option or not far_term_option:
        print(f"Could not find matching options for both expiries at strike ${atm_strike}.")
        return None

    return {
        "ticker": ticker,
        "current_price": current_price,
        "strike_price": atm_strike,
        "near_leg": near_term_option,
        "far_leg": far_term_option
    }

def analyze_and_filter_spread(spread_candidate):
    """
    Analyzes a spread candidate against the screening criteria (liquidity, IV, credit).
    """
    if not spread_candidate:
        return None
        
    near_leg = spread_candidate['near_leg']
    far_leg = spread_candidate['far_leg']

    # Extract relevant data from the legs
    near_quote = near_leg.get('last_quote', {})
    far_quote = far_leg.get('last_quote', {})
    near_greeks = near_leg.get('greeks', {})
    far_greeks = far_leg.get('greeks', {})
    
    # --- Data Extraction ---
    near_bid = near_quote.get('bid', 0)
    far_ask = far_quote.get('ask', 0)
    near_iv = near_greeks.get('implied_volatility', 0)
    far_iv = far_greeks.get('implied_volatility', 0)
    near_theta = near_greeks.get('theta', 0)
    far_theta = far_greeks.get('theta', 0)
    near_volume = near_leg.get('day', {}).get('volume', 0)
    near_oi = near_leg.get('open_interest', 0)
    far_volume = far_leg.get('day', {}).get('volume', 0)
    far_oi = far_leg.get('open_interest', 0)

    # --- Screening Criteria ---
    # 1. Liquidity Check
    if not (near_volume >= MIN_VOLUME and near_oi >= MIN_OPEN_INTEREST and \
            far_volume >= MIN_VOLUME and far_oi >= MIN_OPEN_INTEREST):
        print(f"  - FAILED: Insufficient liquidity for {spread_candidate['ticker']} at strike {spread_candidate['strike_price']}.")
        return None

    # 2. Net Credit Check: We want to receive money for opening the spread.
    #    Sell the near-term (at bid) and buy the far-term (at ask).
    net_credit = near_bid - far_ask
    if net_credit <= 0:
        print(f"  - FAILED: Spread for {spread_candidate['ticker']} is a net debit, not credit.")
        return None

    # 3. Implied Volatility Check: We want higher IV on the option we are selling.
    if near_iv <= far_iv:
        print(f"  - FAILED: Near-term IV ({near_iv:.2f}) is not higher than far-term IV ({far_iv:.2f}).")
        return None
        
    # 4. Theta Check: We want positive theta decay (time works in our favor).
    #    Net Theta = (-1 * theta of short option) + (theta of long option)
    net_theta = (-1 * near_theta) + far_theta
    if net_theta <= 0:
        print(f"  - FAILED: Net theta ({net_theta:.4f}) is not positive.")
        return None
        
    print(f"  - SUCCESS: Found a potential spread for {spread_candidate['ticker']}!")

    return {
        "Ticker": spread_candidate['ticker'],
        "Stock Price": f"${spread_candidate['current_price']:.2f}",
        "Strike": spread_candidate['strike_price'],
        "Near Expiry": near_leg['details']['expiration_date'],
        "Far Expiry": far_leg['details']['expiration_date'],
        "Net Credit": f"${net_credit:.2f}",
        "Net Theta": f"{net_theta:.4f}",
        "IV Diff (Near-Far)": f"{near_iv - far_iv:.4f}",
        "Near IV": f"{near_iv:.2f}",
        "Far IV": f"{far_iv:.2f}",
    }


# --- MAIN EXECUTION ---
def main():
    """
    Main function to run the screener.
    """
    if POLYGON_API_KEY == 'YOUR_API_KEY_HERE':
        print("ERROR: Please replace 'YOUR_API_KEY_HERE' with your actual Polygon.io API key.")
        return

    # Get the next two weekly expiration dates
    try:
        near_expiry, far_expiry = get_next_fridays(2)
    except IndexError:
        print("Could not determine the next two Friday expiration dates. Exiting.")
        return
        
    potential_spreads = []

    for ticker in STOCKS_TO_SCAN:
        candidate = find_atm_options_for_spread(ticker, near_expiry, far_expiry)
        if candidate:
            analyzed_spread = analyze_and_filter_spread(candidate)
            if analyzed_spread:
                potential_spreads.append(analyzed_spread)
    
    # --- Display Results ---
    if not potential_spreads:
        print("\nNo calendar spreads matching the criteria were found.")
    else:
        results_df = pd.DataFrame(potential_spreads)
        # Sort by the highest credit
        results_df['Net Credit Num'] = results_df['Net Credit'].replace({'\$': ''}, regex=True).astype(float)
        results_df = results_df.sort_values(by="Net Credit Num", ascending=False).drop(columns=['Net Credit Num'])
        
        print("\n--- Potential Calendar Spread Opportunities ---")
        print(results_df.to_string(index=False))

if __name__ == "__main__":
    main()

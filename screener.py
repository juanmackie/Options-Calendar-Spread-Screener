import os
import requests
import pandas as pd
from datetime import date, timedelta
import time

# --- CONFIGURATION ---
# IMPORTANT: Add your Polygon.io API key here. You can get a free key from their website.
# It's recommended to set this as an environment variable for security.
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'YOUR_API_KEY_HERE')

# --- SCREENING PARAMETERS ---
# Modify these parameters to change the screener's behavior.

# List of stock tickers to scan.
# Ideally, this could be dynamic (e.g., from a file or sentiment analysis).
STOCKS_TO_SCAN = ['AAPL', 'TSLA', 'NVDA', 'QQQ', 'SPY', 'AMD']

# Minimum option volume for each leg.
MIN_OPTION_VOLUME = 100
# Minimum option open interest for each leg.
MIN_OPTION_OPEN_INTEREST = 500
# Minimum net credit required for the spread (e.g., 0.01 for at least $1 credit).
MIN_NET_CREDIT = 0.01
# Minimum difference by which near-term IV must exceed far-term IV.
MIN_IV_PREMIUM_NEAR_OVER_FAR = 0.00 # e.g., 0.05 for 5% IV premium
# Whether net theta for the spread must be positive.
REQUIRE_POSITIVE_NET_THETA = True
# Type of options contract to scan: 'call', 'put'.
# Support for 'both' can be added later by modifying the main loop.
CONTRACT_TYPE_TO_SCAN = 'call'


# --- API HELPER ---
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 5

def make_api_request(url: str, attempts: int = DEFAULT_RETRY_ATTEMPTS, delay: int = DEFAULT_RETRY_DELAY_SECONDS, backoff_factor: float = 2.0) -> dict | None:
    """
    Makes an HTTP GET request to the given URL with retry logic.
    Handles common request exceptions and retries with exponential backoff.
    """
    for attempt in range(attempts):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            # Specific handling for HTTP errors (e.g., 404, 500)
            print(f"HTTP error occurred: {http_err} - URL: {url}")
            if response.status_code == 401: # Unauthorized, likely API key issue
                print("API Key error (401). Please check your POLYGON_API_KEY.")
                return None # No point retrying if API key is bad
            if response.status_code == 404: # Not found
                print(f"Resource not found at {url}.")
                return None # No point retrying if resource doesn't exist
            # For other HTTP errors, retry might help (e.g., temporary server issues)
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err} - URL: {url}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err} - URL: {url}")
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected error occurred during request: {req_err} - URL: {url}")

        if attempt < attempts - 1:
            sleep_time = delay * (backoff_factor ** attempt)
            print(f"Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        else:
            print(f"Failed to fetch data from {url} after {attempts} attempts.")
            return None
    return None # Should be unreachable if loop completes, but as a fallback


# --- HELPER FUNCTIONS ---

def get_next_fridays(n: int = 2) -> list[str]:
    """
    Calculates the next 'n' upcoming Fridays from today.
    If today is a Friday, it will start with the *next* Friday.
    These dates are typical weekly option expiration dates.
    """
    fridays = []
    today = date.today()

    # Calculate days until the next Friday. Friday is weekday 4.
    days_to_next_friday = (4 - today.weekday() + 7) % 7

    # If today is Friday (days_to_next_friday would be 0),
    # we want to start from the following week's Friday.
    if days_to_next_friday == 0:
        days_to_next_friday = 7

    current_friday = today + timedelta(days=days_to_next_friday)

    for i in range(n):
        fridays.append(current_friday + timedelta(weeks=i))
    return [d.strftime('%Y-%m-%d') for d in fridays]

def get_stock_price(ticker: str) -> float:
    """
    Fetches the last traded price for a given stock ticker using the Polygon API.
    Used as a fallback if price is not in the options snapshot.
    Returns 0.0 if the price cannot be fetched or an error occurs.
    """
    url = f"https://api.polygon.io/v2/last/trade/{ticker}?apiKey={POLYGON_API_KEY}"
    data = make_api_request(url)

    if data:
        try:
            # Ensure 'results' exists and is a dictionary, and 'p' (price) is in 'results'
            if isinstance(data.get('results'), dict) and 'p' in data['results']:
                return float(data['results']['p'])
            else:
                print(f"Price data not found in expected format for {ticker} in response: {data}")
        except (TypeError, ValueError) as e:
            print(f"Error parsing price data for {ticker}: {e} - Data: {data}")
        except KeyError as e:
            print(f"KeyError parsing price data for {ticker}: Missing key {e} - Data: {data}")

    print(f"Could not fetch stock price for {ticker}.")
    return 0.0

def find_atm_options_for_spread(ticker: str, near_expiry: str, far_expiry: str, contract_type_to_search: str) -> dict | None:
    """
    Finds potential At-The-Money (ATM) calendar spreads for a given stock and contract type.

    This function fetches the full option chain for a ticker, identifies the ATM strike,
    and then finds the corresponding options for the near and far expiries for the specified contract type.
    It returns a dictionary containing the spread candidate details or None if not found or an error occurs.
    """
    print(f"\nScanning {ticker} for {contract_type_to_search.upper()} spreads between {near_expiry} and {far_expiry}...")

    # 1. Fetch the entire options snapshot for the ticker
    options_snapshot_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/options/tickers/{ticker}?apiKey={POLYGON_API_KEY}"
    options_data = make_api_request(options_snapshot_url)

    if not options_data:
        print(f"Failed to fetch options snapshot for {ticker}. Skipping.")
        return None

    ticker_options = options_data.get('tickers')
    if not isinstance(ticker_options, list) or not ticker_options:
        print(f"No options contracts found for {ticker} in snapshot data, or data is malformed. Response: {options_data}")
        return None

    # 2. Try to get current stock price from the snapshot's first option's underlying asset details
    current_price = 0.0
    try:
        underlying_asset_info = ticker_options[0].get('underlyingAsset', {})
        if isinstance(underlying_asset_info, dict) and 'price' in underlying_asset_info:
            current_price = float(underlying_asset_info['price'])
            print(f"Extracted current {ticker} price from snapshot: ${current_price:.2f}")
        else:
            print(f"Underlying price not found in snapshot for {ticker}. Attempting fallback.")
    except (TypeError, ValueError, IndexError) as e:
        print(f"Error extracting underlying price from snapshot for {ticker}: {e}. Attempting fallback.")

    if current_price == 0.0: # Fallback if not found or error
        current_price = get_stock_price(ticker)
        if not current_price: # If get_stock_price also returns 0.0 or fails
            print(f"Could not get current price for {ticker} via snapshot or direct call. Skipping.")
            return None
        print(f"Fetched {ticker} price via fallback API call: ${current_price:.2f}")
    else:
        print(f"Current {ticker} price (from snapshot): ${current_price:.2f}")


    # 3. Find the ATM strike price
    all_strikes = []
    try:
        for option_contract in ticker_options:
            if isinstance(option_contract.get('details'), dict) and 'strike_price' in option_contract['details']:
                all_strikes.append(option_contract['details']['strike_price'])
            else:
                # Log if a contract is missing details or strike_price, but continue processing others
                print(f"Warning: Skipping option contract due to missing 'details' or 'strike_price': {option_contract}")

        if not all_strikes:
            print(f"No valid strikes found for {ticker} after parsing options. Snapshot might be incomplete or malformed.")
            return None
        all_strikes = sorted(list(set(all_strikes))) # Deduplicate and sort

    except (TypeError, KeyError) as e:
        print(f"Error processing strikes for {ticker}: {e}. Options data: {ticker_options}")
        return None
        
    atm_strike = min(all_strikes, key=lambda x: abs(x - current_price))
    print(f"Identified At-The-Money (ATM) strike: ${atm_strike}")

    # 4. Find the near-term and far-term options at the ATM strike
    near_term_option = None
    far_term_option = None

    for option_contract in ticker_options:
        details = option_contract.get('details', {})
        # Ensure details is a dictionary before trying to access its items
        if not isinstance(details, dict):
            print(f"Warning: Skipping option contract due to malformed 'details': {option_contract}")
            continue

        if details.get('strike_price') == atm_strike and \
           details.get('contract_type', '').lower() == contract_type_to_search.lower():
            if details.get('expiration_date') == near_expiry:
                near_term_option = option_contract
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

def extract_detailed_option_data(option_leg: dict) -> dict:
    """
    Extracts detailed quote, greeks, and other relevant data from a single option leg.
    Returns a dictionary with extracted data, using 0.0, 0, or None for missing values
    if not found in the provided option leg data.
    """
    if not option_leg: # Should ideally not happen if called with valid data by upstream checks
        # Return a structure with defaults to prevent downstream errors if somehow called with None/empty
        return {
            "bid": 0.0, "ask": 0.0, "mid": 0.0, "iv": 0.0, "theta": 0.0, # Quotes & Greeks
            "delta": 0.0, "gamma": 0.0, "vega": 0.0, # More Greeks
            "volume": 0, "oi": 0, # Activity
            "expiry_date": None, "strike_price": None, "contract_type": None,
            "underlying_ticker": None
        }

    quote = option_leg.get('last_quote', {})
    greeks = option_leg.get('greeks', {})
    details = option_leg.get('details', {})
    day_data = option_leg.get('day', {})

    return {
        "bid": quote.get('bid', 0.0),
        "ask": quote.get('ask', 0.0),
        "mid": quote.get('midpoint', 0.0),
        "iv": greeks.get('implied_volatility', 0.0),
        "theta": greeks.get('theta', 0.0),
        "delta": greeks.get('delta', 0.0),
        "gamma": greeks.get('gamma', 0.0),
        "vega": greeks.get('vega', 0.0),
        "volume": day_data.get('volume', 0),
        "oi": option_leg.get('open_interest', 0),
        "expiry_date": details.get('expiration_date'),
        "strike_price": details.get('strike_price'),
        "contract_type": details.get('contract_type'),
        "underlying_ticker": details.get('underlying_asset', {}).get('ticker') # Polygon v2 snapshot
    }


def filter_spread_candidate(spread_info: dict, near_leg_data: dict, far_leg_data: dict, contract_type: str) -> tuple[bool, str | None, dict | None]:
    """
    Filters the spread candidate based on pre-defined criteria for a specific contract type.
    Returns (is_good_spread, failure_reason, result_dict).
    """
    # Unpack data for easier access
    ticker = spread_info['ticker']
    stock_price = spread_info['current_price']
    strike_price = spread_info['strike_price'] # This is the ATM strike for the spread

    near_bid = near_leg_data["bid"]
    near_iv = near_leg_data["iv"]
    near_theta = near_leg_data["theta"]
    near_volume = near_leg_data["volume"]
    near_oi = near_leg_data["oi"]
    near_expiry = near_leg_data["expiry_date"]

    far_ask = far_leg_data["ask"]
    far_iv = far_leg_data["iv"]
    far_theta = far_leg_data["theta"]
    far_volume = far_leg_data["volume"]
    far_oi = far_leg_data["oi"]
    far_expiry = far_leg_data["expiry_date"]

    # --- Screening Criteria ---
    # 1. Liquidity Check
    if not (near_volume >= MIN_OPTION_VOLUME and near_oi >= MIN_OPTION_OPEN_INTEREST and \
            far_volume >= MIN_OPTION_VOLUME and far_oi >= MIN_OPTION_OPEN_INTEREST):
        reason = (f"Liquidity Failed for {ticker} @ S:{strike_price} ({contract_type.upper()}) - "
                  f"Near (V:{near_volume}<{MIN_OPTION_VOLUME} O:{near_oi}<{MIN_OPTION_OPEN_INTEREST}), "
                  f"Far (V:{far_volume}<{MIN_OPTION_VOLUME} O:{far_oi}<{MIN_OPTION_OPEN_INTEREST})")
        return False, reason, None

    # 2. Net Credit Check
    net_credit = near_bid - far_ask # Selling near-term, buying far-term
    if net_credit < MIN_NET_CREDIT:
        reason = (f"Net Credit Failed for {ticker} @ S:{strike_price} ({contract_type.upper()}) - "
                  f"Credit: {net_credit:.2f} (Required: >{MIN_NET_CREDIT:.2f})")
        return False, reason, None

    # 3. Implied Volatility Premium Check
    iv_difference = near_iv - far_iv
    if iv_difference < MIN_IV_PREMIUM_NEAR_OVER_FAR:
        reason = (f"IV Premium Failed for {ticker} @ S:{strike_price} ({contract_type.upper()}) - "
                  f"IV Diff: {iv_difference:.4f} (Near:{near_iv:.2f}, Far:{far_iv:.2f}, Required: >{MIN_IV_PREMIUM_NEAR_OVER_FAR:.4f})")
        return False, reason, None
        
    # 4. Net Theta Check (Time Decay)
    # Theta for short option (near_leg) is positive for P/L, theta for long option (far_leg) is negative for P/L.
    # Our net_theta should be: theta_of_short_leg - theta_of_long_leg
    # Polygon returns theta as negative for long calls/puts. So, (-near_theta) - (-far_theta) = far_theta - near_theta
    # This is if both thetas are negative.
    # Let's assume: we sell near term (want its theta to benefit us, i.e. if it's -0.1, decay is 0.1/day)
    # we buy far term (its theta hurts us, i.e. if it's -0.05, decay is -0.05/day)
    # Net effect = (-1 * near_theta) + far_theta (This was the original logic and seems correct for Polygon's typical representation)
    net_theta = (-1 * near_theta) + far_theta
    if REQUIRE_POSITIVE_NET_THETA and net_theta <= 0:
        reason = (f"Net Theta Failed for {ticker} @ S:{strike_price} ({contract_type.upper()}) - "
                  f"Net Theta: {net_theta:.4f} (Required > 0 if enabled)")
        return False, reason, None
        
    # If all checks pass:
    result = {
        "Ticker": ticker,
        "Stock Price": f"${stock_price:.2f}",
        "Strike": strike_price,
        "Near Expiry": near_expiry,
        "Far Expiry": far_expiry,
        "Net Credit": f"${net_credit:.2f}", # Store formatted
        "_NetCreditNum": net_credit, # Store numeric for sorting
        "Net Theta": f"{net_theta:.4f}",
        "IV Diff (Near-Far)": f"{iv_difference:.4f}",
        "Near IV": f"{near_iv:.2f}",
        "Far IV": f"{far_iv:.2f}",
        "Contract Type": contract_type.upper()
    }
    return True, None, result


# --- MAIN EXECUTION ---
def main() -> None:
    """
    Main function to initialize and run the options calendar spread screener.
    It sets up parameters, iterates through specified tickers and contract types,
    filters potential spreads, and prints the results.
    """
    if POLYGON_API_KEY == 'YOUR_API_KEY_HERE':
        print("ERROR: Please replace 'YOUR_API_KEY_HERE' with your actual Polygon.io API key in the script or as an environment variable.")
        return

    # Get the next two weekly expiration dates
    try:
        # For calendar spreads, we typically want at least a week between expirations.
        # get_next_fridays(2) gives next Friday and the one after.
        expiries = get_next_fridays(n=2)
        if len(expiries) < 2:
            print("Could not determine two distinct upcoming Friday expiration dates. Exiting.")
            return
        near_expiry, far_expiry = expiries[0], expiries[1]
    except IndexError: # Should be caught by the len check above, but as a safeguard.
        print("Could not determine the next two Friday expiration dates. Exiting.")
        return
        
    print(f"Scanning for spreads with near expiry {near_expiry} and far expiry {far_expiry}.")
    potential_spreads = []

    # Determine which contract types to scan based on configuration
    contract_types_to_process = []
    if CONTRACT_TYPE_TO_SCAN.lower() == 'both':
        contract_types_to_process = ['call', 'put']
    elif CONTRACT_TYPE_TO_SCAN.lower() in ['call', 'put']:
        contract_types_to_process = [CONTRACT_TYPE_TO_SCAN.lower()]
    else:
        print(f"Warning: Invalid CONTRACT_TYPE_TO_SCAN value: '{CONTRACT_TYPE_TO_SCAN}'. Defaulting to 'call'.")
        contract_types_to_process = ['call']

    for contract_type in contract_types_to_process:
        print(f"\n--- Starting scan for {contract_type.upper()} options ---")
        for ticker in STOCKS_TO_SCAN:
            spread_info_candidate = find_atm_options_for_spread(ticker, near_expiry, far_expiry, contract_type)

            if spread_info_candidate:
                near_leg_full_data = spread_info_candidate.get('near_leg')
                far_leg_full_data = spread_info_candidate.get('far_leg')

                if not near_leg_full_data or not far_leg_full_data:
                    print(f"Warning: Incomplete spread candidate for {ticker} ({contract_type.upper()}), missing one or both legs. Skipping.")
                    continue

                near_leg_extracted_data = extract_detailed_option_data(near_leg_full_data)
                far_leg_extracted_data = extract_detailed_option_data(far_leg_full_data)

                if not near_leg_extracted_data or not far_leg_extracted_data:
                    print(f"Warning: Failed to extract data from one or both legs for {ticker} ({contract_type.upper()}). Skipping.")
                    continue

                is_good_spread, reason, result_dict = filter_spread_candidate(
                    spread_info_candidate, # Contains ticker, current_price, strike_price
                    near_leg_extracted_data,
                    far_leg_extracted_data,
                    contract_type
                )

                if is_good_spread and result_dict:
                    print(f"  SUCCESS: Found potential {contract_type.upper()} spread for {ticker} @ Strike {spread_info_candidate['strike_price']}")
                    potential_spreads.append(result_dict)
                elif reason:
                    print(f"  - FILTERED: {reason}") # Reason already includes ticker, strike, contract type
    
    # --- Display Results ---
    if not potential_spreads:
        print(f"\nNo calendar spreads matching the criteria were found across all scanned contract types.")
    else:
        results_df = pd.DataFrame(potential_spreads)
        # Sort by the highest credit (using the numeric field directly)
        results_df = results_df.sort_values(by="_NetCreditNum", ascending=False)
        # Drop the helper column before display
        results_df_display = results_df.drop(columns=['_NetCreditNum'])
        
        # Build a dynamic title for the results based on what was scanned
        scanned_types_str = " & ".join(ct.upper() for ct in contract_types_to_process)
        print(f"\n--- Potential {scanned_types_str} Calendar Spread Opportunities ---")
        print(results_df_display.to_string(index=False))

if __name__ == "__main__":
        print(results_df.to_string(index=False))

if __name__ == "__main__":
    main()

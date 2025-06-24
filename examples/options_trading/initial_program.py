"""
Initial program for an options trading algorithm.
This program defines a basic structure for generating trades based on market data.
The core trading logic is intended to be evolved by OpenEvolve.
"""
import random
import pandas as pd # Assuming data might be in pandas DataFrame

# Placeholder for any global parameters or configurations if needed
# For example, risk limits, preferred option types, etc.
# These could also be part of the 'parameters' dict passed to generate_trades.

# EVOLVE-BLOCK-START
# The core trading logic to be evolved resides in this block.
# Initially, it will be a very simple or random strategy.

def decide_action(option_data, parameters):
    """
    Decides on an action for a given option.
    This is a very basic random decision maker.

    Args:
        option_data (dict): Data for a specific option contract.
                            Example: {'symbol': 'SPY251231C00500000', 'type': 'call',
                                      'strike': 500, 'expiry': '2025-12-31',
                                      'bid': 10.0, 'ask': 10.5, 'underlying_price': 490,
                                      'iv': 0.20, 'delta': 0.6, 'gamma': 0.02,
                                      'theta': -0.05, 'vega': 0.1}
        parameters (dict): Algorithm parameters.
                           Example: {'risk_per_trade': 0.01, 'min_delta': 0.3}

    Returns:
        dict or None: A trade action or None if no action.
                      Example: {'action': 'BUY', 'contract': option_data, 'quantity': 1}
    """
    action_choice = random.choice(["BUY_CALL", "BUY_PUT", "SELL_CALL", "SELL_PUT", "HOLD"])

    if action_choice == "BUY_CALL" and option_data['type'] == 'call':
        if option_data['ask'] > 0 and parameters.get('enable_buys', True): # Ensure ask price is positive
            return {'action': 'BUY', 'contract_symbol': option_data['symbol'], 'quantity': 1, 'price': option_data['ask']}
    elif action_choice == "BUY_PUT" and option_data['type'] == 'put':
        if option_data['ask'] > 0 and parameters.get('enable_buys', True):
            return {'action': 'BUY', 'contract_symbol': option_data['symbol'], 'quantity': 1, 'price': option_data['ask']}
    # Note: Selling options (especially uncovered) is complex and risky.
    # Initial simple version might focus on buying or be very conservative with selling.
    # For now, we'll keep it simple. More sophisticated selling logic can be evolved.
    elif action_choice == "SELL_CALL" and option_data['type'] == 'call':
        if option_data['bid'] > 0 and parameters.get('enable_sells', False): # Selling might be disabled by default
             return {'action': 'SELL', 'contract_symbol': option_data['symbol'], 'quantity': 1, 'price': option_data['bid']}
    elif action_choice == "SELL_PUT" and option_data['type'] == 'put':
        if option_data['bid'] > 0 and parameters.get('enable_sells', False):
             return {'action': 'SELL', 'contract_symbol': option_data['symbol'], 'quantity': 1, 'price': option_data['bid']}
    return None

def generate_trades_logic(historical_data, current_holdings, parameters):
    """
    Core logic for generating trades. This function will be evolved.

    Args:
        historical_data (pd.DataFrame or list of dicts):
            Historical market data. Could include:
            - For underlying: Timestamp, Open, High, Low, Close, Volume
            - For options: Timestamp, OptionSymbol, Type, Strike, Expiry, Bid, Ask, Volume, IV, Greeks
            Example for one timestamp, one option:
            [{'timestamp': '2023-01-01 09:30:00', 'underlying_price': 100,
              'options_chain': [
                  {'symbol': 'XYZ231231C00100000', 'type': 'call', 'strike': 100, ...},
                  {'symbol': 'XYZ231231P00100000', 'type': 'put', 'strike': 100, ...}
              ]
            }]
            The exact structure will depend on the data source from the API.

        current_holdings (list of dicts):
            Current positions in the portfolio.
            Example: [{'symbol': 'SPY251231C00500000', 'quantity': 10, 'entry_price': 9.5}]

        parameters (dict):
            Parameters to guide the trading strategy.
            Example: {'max_risk_per_trade': 0.01, 'target_profit_pct': 0.20}

    Returns:
        list of dicts: A list of trade orders.
                       Example: [{'action': 'BUY', 'contract_symbol': 'SPY251231C00500000', 'quantity': 1, 'limit_price': 10.5, 'order_type': 'LIMIT'}]
                       Example: [{'action': 'SELL', 'contract_symbol': 'SPY251231C00500000', 'quantity': 1, 'limit_price': 10.0, 'order_type': 'LIMIT'}]
    """
    trades = []

    # This is a very naive example:
    # It looks at the latest options data available and makes a random decision for the first few options.
    # A real strategy would analyze historical_data, current_holdings, and use parameters.

    if not historical_data:
        return trades

    # Assume historical_data is a list of snapshots, and the last one is the most current.
    latest_snapshot = historical_data[-1]

    if 'options_chain' in latest_snapshot:
        options_to_consider = latest_snapshot['options_chain'][:5] # Look at first 5 options for simplicity

        for option_data in options_to_consider:
            # Basic check for necessary data
            if not all(k in option_data for k in ['symbol', 'type', 'strike', 'bid', 'ask']):
                continue

            action = decide_action(option_data, parameters)
            if action:
                # Add order type, default to Market Order if not specified by decide_action
                action['order_type'] = action.get('order_type', 'MARKET')
                trades.append(action)

    # Limit number of trades for this simple example
    return trades[:parameters.get('max_trades_per_step', 1)]

# EVOLVE-BLOCK-END

# This part remains fixed (not evolved)
# It ensures that OpenEvolve can consistently call the evolving function.
def get_trading_algorithm():
    """
    Returns the current trading algorithm function.
    This function should not be modified by the LLM.
    """
    return generate_trades_logic

# Example usage (for testing the initial program structure)
if __name__ == "__main__":
    # Mock data for testing
    mock_historical_data = [
        {'timestamp': '2023-10-01 09:30:00', 'underlying_price': 450.00,
         'options_chain': [
             {'symbol': 'SPY251231C00450000', 'type': 'call', 'strike': 450, 'expiry': '2025-12-31', 'bid': 20.0, 'ask': 20.5, 'underlying_price': 450, 'iv': 0.18, 'delta': 0.5, 'gamma': 0.01, 'theta': -0.03, 'vega': 0.15},
             {'symbol': 'SPY251231P00450000', 'type': 'put', 'strike': 450, 'expiry': '2025-12-31', 'bid': 18.0, 'ask': 18.5, 'underlying_price': 450, 'iv': 0.19, 'delta': -0.45, 'gamma': 0.01, 'theta': -0.03, 'vega': 0.15},
             {'symbol': 'SPY251231C00460000', 'type': 'call', 'strike': 460, 'expiry': '2025-12-31', 'bid': 15.0, 'ask': 15.5, 'underlying_price': 450, 'iv': 0.17, 'delta': 0.4, 'gamma': 0.01, 'theta': -0.03, 'vega': 0.14},
         ]},
        {'timestamp': '2023-10-01 09:31:00', 'underlying_price': 450.50,
         'options_chain': [
             {'symbol': 'SPY251231C00450000', 'type': 'call', 'strike': 450, 'expiry': '2025-12-31', 'bid': 20.2, 'ask': 20.7, 'underlying_price': 450.50, 'iv': 0.18, 'delta': 0.51, 'gamma': 0.01, 'theta': -0.03, 'vega': 0.15},
             {'symbol': 'SPY251231P00450000', 'type': 'put', 'strike': 450, 'expiry': '2025-12-31', 'bid': 17.8, 'ask': 18.3, 'underlying_price': 450.50, 'iv': 0.19, 'delta': -0.44, 'gamma': 0.01, 'theta': -0.03, 'vega': 0.15},
         ]}
    ]
    mock_current_holdings = []
    mock_parameters = {
        'max_risk_per_trade': 0.02,
        'target_profit_pct': 0.15,
        'enable_buys': True,
        'enable_sells': True, # Allow selling for test
        'max_trades_per_step': 2
    }

    trading_algorithm = get_trading_algorithm()
    suggested_trades = trading_algorithm(mock_historical_data, mock_current_holdings, mock_parameters)

    print("Suggested Trades:")
    if suggested_trades:
        for trade in suggested_trades:
            print(f"- {trade['action']} {trade['quantity']} of {trade['contract_symbol']} at {trade['price']} ({trade['order_type']})")
    else:
        print("No trades suggested.")

# Options Trading Algorithm Evolution with OpenEvolve

This example demonstrates how to use OpenEvolve to evolve Python-based options trading algorithms. The goal is to discover strategies that maximize profitability and other relevant trading metrics through an evolutionary process.

## Overview

The system works by:
1.  **Initial Program**: Starting with a basic options trading strategy.
2.  **Evaluation (Backtesting)**: Testing the performance of each algorithm against historical options data using an API. Metrics like profit/loss, Sharpe ratio, max drawdown, etc., are calculated.
3.  **LLM-based Evolution**: Using Large LanguageModels to analyze the performance and code of existing algorithms and suggest modifications or new strategies.
4.  **Iteration**: Repeating the evaluation and evolution process to continuously improve the trading algorithms.

## Components

*   `initial_program.py`: Contains the starting template for an options trading algorithm. The LLM will evolve the logic within the `# EVOLVE-BLOCK-START` and `# EVOLVE-BLOCK-END` markers.
*   `evaluator.py`: Responsible for backtesting trading algorithms. It will interface with an external API to fetch historical options data and simulate trades.
*   `config.yaml`: Configuration file for OpenEvolve, including LLM settings, prompt details, and evolutionary parameters tailored for options trading.
*   `requirements.txt`: Lists Python dependencies needed for this example.

## How to Run

1.  **Set up API Access**: Ensure your environment is configured with the necessary credentials and endpoint for the options data API that `evaluator.py` will use.
2.  **Install Dependencies**:
    ```bash
    pip install -r examples/options_trading/requirements.txt
    ```
3.  **Run OpenEvolve**:
    Navigate to the root of the OpenEvolve project and run:
    ```bash
    python openevolve-run.py examples/options_trading/initial_program.py examples/options_trading/evaluator.py --config examples/options_trading/config.yaml
    ```

## Key Metrics for Evaluation

The `evaluator.py` will aim to calculate metrics such as:
*   Total Profit/Loss
*   Sharpe Ratio
*   Maximum Drawdown
*   Win Rate
*   Number of Trades
*   Average Profit per Trade
*   `combined_score`: A composite score used by OpenEvolve for selection.

## Customization

*   **Data Source**: Modify `evaluator.py` to connect to your specific options data API and handle its data format.
*   **Initial Strategy**: Update `initial_program.py` with a different baseline strategy if desired.
*   **LLM Prompts**: Adjust the `system_message` in `config.yaml` to guide the LLM's evolution process differently.
*   **Metrics**: Add or modify performance metrics in `evaluator.py` to suit your trading objectives.

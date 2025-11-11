# fin-wallet-tracker

A simple Python-based portfolio tracker that visualizes stock holdings over time.

## Overview

This tool parses a CSV file containing stock purchase transactions and generates an interactive HTML chart showing your portfolio's value at the beginning of each month from your earliest purchase to today. Historical prices are fetched from Yahoo Finance and cached locally for efficient reuse.

## Features

- **Tickers**: Fetch historical prices once and reuse them when adding new transactions

## Quick Start

```bash
make install    # Install dependencies
make run        # Fetch prices, build portfolio, and open in browser
```

Add your transactions to `my-tickers.csv` and run `make run` to see your portfolio growth!

## How It Works

The project uses a **two-step workflow** to efficiently manage price data:

### Step 1: Fetch Prices (`make fetch`)
- Scans `my-tickers.csv` for unique ticker symbols
- Fetches historical prices from Yahoo Finance
- Saves prices to `prices.csv` (cached for reuse)
- Only fetches prices that don't already exist in the cache

### Step 2: Build Portfolio (`make build`)
- Reads transactions from `my-tickers.csv`
- Loads cached prices from `prices.csv`
- Calculates portfolio value over time
- Generates `portfolio_data.json` with detailed holdings
- Creates `portfolio.html` with interactive chart

**Why two steps?** This separation means you can add new transactions without re-fetching historical prices from Yahoo Finance, making updates much faster!

## Input Format

Create `my-tickers.csv` with your transactions:

```csv
ticker,purchase_date,quantity,price,transaction_fees
AAPL,2023-11-03,10,170.0,1.0
VHVE.L,2023-01-03,7,75.0,1.0
```

**Columns:**
- `ticker` - Stock ticker symbol (e.g., AAPL, MSFT, VHVE.L for London stocks)
- `purchase_date` - Date of purchase in YYYY-MM-DD format
- `quantity` - Number of shares purchased
- `price` - Purchase price per share
- `transaction_fees` - Brokerage fees for the transaction

## Available Commands

```bash
make help          # Show all available commands
make install       # Install Python dependencies
make fetch         # Fetch prices from Yahoo Finance
make build         # Prepare data and generate HTML
make run           # Run both fetch and build, then open in browser
make open          # Open portfolio.html in browser
make view-csv      # Display your transactions
make view-prices   # Display cached prices
make view-data     # Display portfolio data JSON
make test-ticker   # Test fetching a specific ticker
make clean         # Remove generated files
```

## Examples

### First time setup:
```bash
# 1. Create your transactions file
cat > my-tickers.csv << EOF
ticker,purchase_date,quantity,price,transaction_fees
AAPL,2023-11-03,10,170.0,1.0
EOF

# 2. Run everything
make run
```

### Adding new transactions:
```bash
# 1. Add a new line to my-tickers.csv
echo "MSFT,2024-01-15,5,380.0,1.0" >> my-tickers.csv

# 2. Fetch prices for new ticker (if needed)
make fetch

# 3. Rebuild portfolio
make build

# 4. View results
make open
```

### Just updating the visualization:
```bash
# If you only changed transactions (no new tickers)
# you can skip fetching and just rebuild:
make build
make open
```

## Dependencies

- Python 3.x
- yfinance - Yahoo Finance API wrapper
- python-dateutil - Date handling utilities

Install with: `make install` or `pip install -r requirements.txt`

## Notes

- Prices are fetched for the 1st of each month from your earliest purchase to today
- The portfolio value chart shows your total holdings at each month
- London stocks (e.g., VHVE.L) are supported via Yahoo Finance
- Price data is cached in `prices.csv` to avoid unnecessary API calls
- `portfolio_data.json` is gitignored but can be inspected with `make view-data`

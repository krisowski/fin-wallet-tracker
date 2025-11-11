#!/usr/bin/env python3
"""
Stock Price Fetcher - Step 1
Parses my-tickers.csv, fetches historical prices, and saves all data
to portfolio_data.json for manual inspection and later visualization.
"""

import csv
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import json


def parse_csv(filename):
    """Parse the CSV file and return list of transactions."""
    transactions = []
    with open(filename, 'r') as f:
        # Read the raw lines to handle malformed CSV
        lines = f.readlines()

        # Parse data rows manually (skip header)
        for line in lines[1:]:
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            parts = line.split(',')
            if len(parts) >= 5:
                ticker = parts[0]
                purchase_date = datetime.strptime(parts[1], '%Y-%m-%d')
                quantity = float(parts[2])
                purchase_price = float(parts[3])
                transaction_fees = float(parts[4])

                transactions.append({
                    'ticker': ticker,
                    'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                    'quantity': quantity,
                    'purchase_price': purchase_price,
                    'transaction_fees': transaction_fees
                })

    return transactions


def get_earliest_date(transactions):
    """Get the earliest purchase date from transactions."""
    dates = [datetime.strptime(t['purchase_date'], '%Y-%m-%d') for t in transactions]
    return min(dates)


def generate_month_dates(start_date, end_date):
    """Generate list of 1st day of each month between start and end dates."""
    dates = []
    current = start_date.replace(day=1)

    # If start date is not the 1st, move to next month
    if start_date.day > 1:
        current = current + relativedelta(months=1)

    while current <= end_date:
        dates.append(current)
        current = current + relativedelta(months=1)

    return dates


def get_holdings_at_date(transactions, target_date):
    """Calculate total holdings of each ticker up to the target date."""
    holdings = defaultdict(float)

    for transaction in transactions:
        trans_date = datetime.strptime(transaction['purchase_date'], '%Y-%m-%d')
        if trans_date <= target_date:
            holdings[transaction['ticker']] += transaction['quantity']

    return dict(holdings)


def fetch_price(ticker, date):
    """Fetch stock price for a specific ticker on a specific date."""
    try:
        stock = yf.Ticker(ticker)
        # Fetch data for a small window around the target date
        start_date = date - timedelta(days=5)
        end_date = date + timedelta(days=5)

        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            print(f"Warning: No data found for {ticker} around {date}")
            return None

        # Try to get the exact date, or the closest date
        if date.strftime('%Y-%m-%d') in hist.index.strftime('%Y-%m-%d'):
            return hist.loc[date.strftime('%Y-%m-%d')]['Close']
        else:
            # Get the closest date
            return hist.iloc[0]['Close']

    except Exception as e:
        print(f"Error fetching price for {ticker} on {date}: {e}")
        return None


def fetch_portfolio_data(transactions, dates):
    """Fetch prices and calculate portfolio values at each date."""
    portfolio_data = []

    for date in dates:
        holdings = get_holdings_at_date(transactions, date)
        date_data = {
            'date': date.strftime('%Y-%m-%d'),
            'holdings': [],
            'total_value': 0
        }

        print(f"Fetching prices for {date.strftime('%Y-%m-%d')}...")

        for ticker, quantity in holdings.items():
            price = fetch_price(ticker, date)
            if price is not None:
                value = quantity * price
                date_data['holdings'].append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'price': round(price, 2),
                    'value': round(value, 2)
                })
                date_data['total_value'] += value
                print(f"  {ticker}: {quantity} shares × ${price:.2f} = ${value:.2f}")

        date_data['total_value'] = round(date_data['total_value'], 2)
        portfolio_data.append(date_data)
        print(f"  Total: ${date_data['total_value']:.2f}\n")

    return portfolio_data


def save_portfolio_data(transactions, portfolio_data, output_file='portfolio_data.json'):
    """Save portfolio data to JSON file for inspection and later use."""
    output = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'transactions': transactions,
        'portfolio_values': portfolio_data
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Portfolio data saved to: {output_file}")


def main():
    """Main function to fetch and save portfolio data."""
    print("Stock Price Fetcher - Step 1")
    print("=" * 50)

    # Parse CSV
    print("\n1. Parsing CSV file...")
    transactions = parse_csv('my-tickers.csv')
    print(f"   Found {len(transactions)} transactions")

    # Get date range
    print("\n2. Determining date range...")
    earliest_date = get_earliest_date(transactions)
    today = datetime.now()
    print(f"   Earliest purchase: {earliest_date.strftime('%Y-%m-%d')}")
    print(f"   Today: {today.strftime('%Y-%m-%d')}")

    # Generate month dates
    print("\n3. Generating monthly dates...")
    dates = generate_month_dates(earliest_date, today)
    print(f"   Generated {len(dates)} dates")

    # Fetch prices and calculate portfolio values
    print("\n4. Fetching prices and calculating values...")
    portfolio_data = fetch_portfolio_data(transactions, dates)

    # Save to JSON
    print("\n5. Saving data to JSON file...")
    save_portfolio_data(transactions, portfolio_data)

    print("\n" + "=" * 50)
    print("Done! Data saved to portfolio_data.json")
    print("Run 'python build_html.py' to generate the visualization")


if __name__ == '__main__':
    main()

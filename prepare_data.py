#!/usr/bin/env python3
"""
Portfolio Data Preparation - Step 2
Reads my-tickers.csv and prices.csv to prepare portfolio_data.json
for HTML visualization. This allows you to add new transactions without
refetching all prices from Yahoo.
"""

import csv
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict


def parse_transactions(filename):
    """Parse the transactions CSV file."""
    transactions = []

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append({
                'ticker': row['ticker'].strip(),
                'purchase_date': row['purchase_date'].strip(),
                'quantity': float(row['quantity']),
                'purchase_price': float(row['price']),
                'transaction_fees': float(row['transaction_fees'])
            })

    return transactions


def load_prices(filename):
    """Load prices from prices.csv (wide format with date and ticker columns)."""
    prices = {}

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['date']

            # Iterate through all columns except 'date'
            for ticker in row.keys():
                if ticker != 'date' and row[ticker]:
                    if ticker not in prices:
                        prices[ticker] = {}
                    prices[ticker][date] = float(row[ticker])

    return prices


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


def prepare_portfolio_data(transactions, prices, dates):
    """Prepare portfolio data using transactions and pre-fetched prices."""
    portfolio_data = []

    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        holdings = get_holdings_at_date(transactions, date)

        date_data = {
            'date': date_str,
            'holdings': [],
            'total_value': 0
        }

        print(f"Processing {date_str}...")

        for ticker, quantity in holdings.items():
            # Look up price from prices.csv
            if ticker in prices and date_str in prices[ticker]:
                price = prices[ticker][date_str]
                value = quantity * price

                date_data['holdings'].append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'price': round(price, 2),
                    'value': round(value, 2)
                })
                date_data['total_value'] += value
                print(f"  {ticker}: {quantity} shares × ${price:.2f} = ${value:.2f}")
            else:
                print(f"  Warning: No price found for {ticker} on {date_str}")

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
    """Main function to prepare portfolio data."""
    print("Portfolio Data Preparation - Step 2")
    print("=" * 50)

    # Check if prices.csv exists
    try:
        print("\n1. Loading prices from prices.csv...")
        prices = load_prices('prices.csv')
        total_prices = sum(len(dates) for dates in prices.values())
        print(f"   Loaded {total_prices} price entries for {len(prices)} tickers")
    except FileNotFoundError:
        print("Error: prices.csv not found!")
        print("Please run 'make fetch' first to fetch prices from Yahoo Finance.")
        exit(1)

    # Parse transactions
    print("\n2. Parsing transactions from my-tickers.csv...")
    transactions = parse_transactions('my-tickers.csv')
    print(f"   Found {len(transactions)} transactions")

    # Get date range
    print("\n3. Determining date range...")
    earliest_date = get_earliest_date(transactions)
    today = datetime.now()
    print(f"   Earliest purchase: {earliest_date.strftime('%Y-%m-%d')}")
    print(f"   Today: {today.strftime('%Y-%m-%d')}")

    # Generate month dates
    print("\n4. Generating monthly dates...")
    dates = generate_month_dates(earliest_date, today)
    print(f"   Generated {len(dates)} dates")

    # Prepare portfolio data
    print("\n5. Preparing portfolio data...")
    portfolio_data = prepare_portfolio_data(transactions, prices, dates)

    # Save to JSON
    print("\n6. Saving data to JSON file...")
    save_portfolio_data(transactions, portfolio_data)

    print("\n" + "=" * 50)
    print("Done! Data saved to portfolio_data.json")
    print("Run 'python build_html.py' to generate the HTML visualization")


if __name__ == '__main__':
    main()

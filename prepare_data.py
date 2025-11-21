#!/usr/bin/env python3
"""
Portfolio Data Preparation - Step 2
Reads my-tickers.csv and prices.csv to prepare portfolio_data.json
for HTML visualization. This allows you to add new transactions without
refetching all prices from Yahoo.
"""

import csv
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict


def parse_transactions(filename):
    """Parse the transactions CSV file."""
    transactions = []

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('ticker', '').strip():
                continue

            transactions.append({
                'ticker': row['ticker'].strip(),
                'purchase_date': row['purchase_date'].strip(),
                'ticker_currency': row.get('ticker_currency', '').strip(),
                'local_currency': row.get('local_currency', '').strip(),
                'quantity': float(row['quantity']),
                'price_in_local_currency': float(row['price_in_local_currency']),
                'fee_in_local_currency': float(row['fee_in_local_currency']),
                'exchange_rate': float(row['exchange_rate'])
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


def load_exchange_rates(filename):
    """Load exchange rates from exchange_rates.csv."""
    rates = {}

    if not os.path.exists(filename):
        return rates

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['date']

            # Iterate through all columns except 'date'
            for pair_key in row.keys():
                if pair_key != 'date' and row[pair_key]:
                    if pair_key not in rates:
                        rates[pair_key] = {}
                    rates[pair_key][date] = float(row[pair_key])

    return rates


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


def convert_value(value, from_currency, to_currency, exchange_rates, date_str):
    """Convert a value from one currency to another using exchange rates."""
    if from_currency == to_currency:
        return value

    pair_key = f"{from_currency}_{to_currency}"
    if pair_key in exchange_rates and date_str in exchange_rates[pair_key]:
        exchange_rate = exchange_rates[pair_key][date_str]
        return value * exchange_rate
    else:
        print(f"  Warning: No exchange rate for {pair_key} on {date_str}")
        return value


def prepare_portfolio_data(transactions, prices, exchange_rates, dates):
    """Prepare portfolio data using transactions, pre-fetched prices, and exchange rates."""
    portfolio_data = []

    # Build a map of ticker -> currency info for quick lookup
    ticker_currency_map = {}
    for transaction in transactions:
        ticker = transaction['ticker']
        if ticker not in ticker_currency_map:
            ticker_currency_map[ticker] = {
                'ticker_currency': transaction['ticker_currency'],
                'local_currency': transaction['local_currency']
            }

    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        holdings = get_holdings_at_date(transactions, date)

        date_data = {
            'date': date_str,
            'holdings': [],
            'total_value_usd': 0,
            'total_value_eur': 0,
            'total_value_pln': 0
        }

        print(f"Processing {date_str}...")

        for ticker, quantity in holdings.items():
            # Look up price from prices.csv
            if ticker in prices and date_str in prices[ticker]:
                price = prices[ticker][date_str]

                # Get currency info for this ticker
                currency_info = ticker_currency_map.get(ticker, {})
                ticker_currency = currency_info.get('ticker_currency', 'USD')
                local_currency = currency_info.get('local_currency', 'PLN')

                # Calculate value in original currency
                value_original = quantity * price

                # Convert to all three display currencies
                price_usd = convert_value(price, ticker_currency, 'USD', exchange_rates, date_str)
                price_eur = convert_value(price, ticker_currency, 'EUR', exchange_rates, date_str)
                price_pln = convert_value(price, ticker_currency, 'PLN', exchange_rates, date_str)

                value_usd = quantity * price_usd
                value_eur = quantity * price_eur
                value_pln = quantity * price_pln

                print(f"  {ticker}: {quantity} shares × {price:.2f} {ticker_currency} = {value_usd:.2f} USD, {value_eur:.2f} EUR, {value_pln:.2f} PLN")

                date_data['holdings'].append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'price_original': round(price, 2),
                    'value_original': round(value_original, 2),
                    'price_usd': round(price_usd, 2),
                    'value_usd': round(value_usd, 2),
                    'price_eur': round(price_eur, 2),
                    'value_eur': round(value_eur, 2),
                    'price_pln': round(price_pln, 2),
                    'value_pln': round(value_pln, 2),
                    'ticker_currency': ticker_currency,
                    'local_currency': local_currency
                })
                date_data['total_value_usd'] += value_usd
                date_data['total_value_eur'] += value_eur
                date_data['total_value_pln'] += value_pln
            else:
                print(f"  Warning: No price found for {ticker} on {date_str}")

        date_data['total_value_usd'] = round(date_data['total_value_usd'], 2)
        date_data['total_value_eur'] = round(date_data['total_value_eur'], 2)
        date_data['total_value_pln'] = round(date_data['total_value_pln'], 2)
        portfolio_data.append(date_data)
        print(f"  Total: {date_data['total_value_usd']:.2f} USD, {date_data['total_value_eur']:.2f} EUR, {date_data['total_value_pln']:.2f} PLN\n")

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

    # Load exchange rates
    print("\n2. Loading exchange rates from exchange_rates.csv...")
    exchange_rates = load_exchange_rates('exchange_rates.csv')
    if exchange_rates:
        total_rates = sum(len(dates) for dates in exchange_rates.values())
        print(f"   Loaded {total_rates} exchange rate entries for {len(exchange_rates)} currency pairs")
    else:
        print("   No exchange rates found (all transactions in same currency)")

    # Parse transactions
    print("\n3. Parsing transactions from my-tickers.csv...")
    transactions = parse_transactions('my-tickers.csv')
    print(f"   Found {len(transactions)} transactions")

    # Get date range
    print("\n4. Determining date range...")
    earliest_date = get_earliest_date(transactions)
    today = datetime.now()
    print(f"   Earliest purchase: {earliest_date.strftime('%Y-%m-%d')}")
    print(f"   Today: {today.strftime('%Y-%m-%d')}")

    # Generate month dates
    print("\n5. Generating monthly dates...")
    dates = generate_month_dates(earliest_date, today)
    print(f"   Generated {len(dates)} dates")

    # Prepare portfolio data
    print("\n6. Preparing portfolio data...")
    portfolio_data = prepare_portfolio_data(transactions, prices, exchange_rates, dates)

    # Save to JSON
    print("\n7. Saving data to JSON file...")
    save_portfolio_data(transactions, portfolio_data)

    print("\n" + "=" * 50)
    print("Done! Data saved to portfolio_data.json")
    print("Run 'python build_html.py' to generate the HTML visualization")


if __name__ == '__main__':
    main()

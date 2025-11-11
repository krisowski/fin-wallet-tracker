#!/usr/bin/env python3
"""
Stock Price Fetcher - Step 1
Scans my-tickers.csv for unique tickers and fetches their historical prices
to prices.csv. This is a separate step so you don't need to refetch all prices
from Yahoo every time you add a new transaction.
"""

import csv
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os


def get_unique_tickers(filename):
    """Parse my-tickers.csv and return list of unique tickers and earliest date."""
    tickers = set()
    earliest_date = None

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row['ticker'].strip()
            if ticker:
                tickers.add(ticker)

            # Track earliest purchase date
            purchase_date = datetime.strptime(row['purchase_date'], '%Y-%m-%d')
            if earliest_date is None or purchase_date < earliest_date:
                earliest_date = purchase_date

    return sorted(list(tickers)), earliest_date


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


def load_existing_prices(filename):
    """Load existing prices from prices.csv if it exists (wide format)."""
    prices = {}

    if not os.path.exists(filename):
        return prices

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


def fetch_and_save_prices(tickers, dates, output_file='prices.csv'):
    """Fetch prices for all tickers and dates, merging with existing data."""
    # Load existing prices
    existing_prices = load_existing_prices(output_file)

    print(f"Found {sum(len(d) for d in existing_prices.values())} existing price entries")

    # Collect all price data in a dict: {date: {ticker: price}}
    price_data = {}
    fetch_count = 0
    skip_count = 0

    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        price_data[date_str] = {}

        for ticker in tickers:
            # Check if we already have this price
            if ticker in existing_prices and date_str in existing_prices[ticker]:
                price = existing_prices[ticker][date_str]
                skip_count += 1
            else:
                # Fetch new price
                price = fetch_price(ticker, date)
                if price is not None:
                    fetch_count += 1
                    print(f"{ticker} {date_str}: ${price:.2f}")
                else:
                    price = None
                    continue

            if price is not None:
                price_data[date_str][ticker] = round(price, 2)

    # Write to CSV in wide format (date, ticker1, ticker2, ...)
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['date'] + tickers
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for date_str in sorted(price_data.keys()):
            row = {'date': date_str}
            row.update(price_data[date_str])
            writer.writerow(row)

    total_entries = sum(len(prices) for prices in price_data.values())
    print(f"\n{'-' * 50}")
    print(f"Prices saved to: {output_file}")
    print(f"Total entries: {total_entries}")
    print(f"Newly fetched: {fetch_count}")
    print(f"Used from cache: {skip_count}")


def main():
    """Main function to fetch and save price data."""
    print("Stock Price Fetcher - Step 1")
    print("=" * 50)

    # Parse CSV for unique tickers
    print("\n1. Scanning my-tickers.csv for unique tickers...")
    tickers, earliest_date = get_unique_tickers('my-tickers.csv')
    print(f"   Found {len(tickers)} unique tickers: {', '.join(tickers)}")
    print(f"   Earliest purchase: {earliest_date.strftime('%Y-%m-%d')}")

    # Generate month dates
    print("\n2. Generating monthly dates...")
    today = datetime.now()
    dates = generate_month_dates(earliest_date, today)
    print(f"   Generated {len(dates)} dates from {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")

    # Fetch and save prices
    print("\n3. Fetching prices (skipping existing ones)...")
    fetch_and_save_prices(tickers, dates)

    print("\n" + "=" * 50)
    print("Done! Run 'make build' to prepare portfolio data and generate HTML")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Exchange Rate Fetcher
Scans my-tickers.csv for currency pairs and fetches their historical exchange rates.
Saves exchange rates to exchange_rates.csv for use in portfolio calculations.
"""

import csv
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os


def get_currency_pairs(filename):
    """Parse my-tickers.csv and return all necessary currency pairs for multi-currency support."""
    currencies_used = set()
    earliest_date = None

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker_currency = row.get('ticker_currency', '').strip()
            local_currency = row.get('local_currency', '').strip()

            if ticker_currency:
                currencies_used.add(ticker_currency)
            if local_currency:
                currencies_used.add(local_currency)

            # Track earliest purchase date
            purchase_date = datetime.strptime(row['purchase_date'], '%Y-%m-%d')
            if earliest_date is None or purchase_date < earliest_date:
                earliest_date = purchase_date

    # Generate all necessary pairs for multi-currency support
    # We need conversions between all unique currencies
    currency_pairs = set()
    currencies_list = sorted(list(currencies_used))

    for i, from_curr in enumerate(currencies_list):
        for to_curr in currencies_list:
            if from_curr != to_curr:
                currency_pairs.add((from_curr, to_curr))

    return sorted(list(currency_pairs)), earliest_date


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


def load_existing_rates(filename):
    """Load existing exchange rates from exchange_rates.csv if it exists."""
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


def fetch_exchange_rate(from_currency, to_currency, date):
    """Fetch exchange rate for a currency pair on a specific date using yfinance."""
    try:
        # yfinance uses format like "USDPLN=X" for currency pairs
        pair_symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(pair_symbol)

        # Fetch data for a small window around the target date
        start_date = date - timedelta(days=5)
        end_date = date + timedelta(days=5)

        hist = ticker.history(start=start_date, end=end_date)

        if hist.empty:
            print(f"Warning: No data found for {from_currency}/{to_currency} around {date}")
            return None

        # Try to get the exact date, or the closest date
        if date.strftime('%Y-%m-%d') in hist.index.strftime('%Y-%m-%d'):
            return hist.loc[date.strftime('%Y-%m-%d')]['Close']
        else:
            # Get the closest date
            return hist.iloc[0]['Close']

    except Exception as e:
        print(f"Error fetching rate for {from_currency}/{to_currency} on {date}: {e}")
        return None


def fetch_and_save_rates(currency_pairs, dates, output_file='exchange_rates.csv'):
    """Fetch exchange rates for all currency pairs and dates."""
    # Load existing rates
    existing_rates = load_existing_rates(output_file)

    if existing_rates:
        print(f"Found {sum(len(d) for d in existing_rates.values())} existing exchange rate entries")

    # Collect all rate data in a dict: {date: {pair_key: rate}}
    rate_data = {}
    fetch_count = 0
    skip_count = 0

    # Generate pair keys for CSV columns
    pair_keys = [f"{from_curr}_{to_curr}" for from_curr, to_curr in currency_pairs]

    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        rate_data[date_str] = {}

        for (from_currency, to_currency), pair_key in zip(currency_pairs, pair_keys):
            # Check if we already have this rate
            if pair_key in existing_rates and date_str in existing_rates[pair_key]:
                rate = existing_rates[pair_key][date_str]
                skip_count += 1
            else:
                # Fetch new rate
                rate = fetch_exchange_rate(from_currency, to_currency, date)
                if rate is not None:
                    fetch_count += 1
                    print(f"{from_currency}/{to_currency} {date_str}: {rate:.4f}")
                else:
                    continue

            if rate is not None:
                rate_data[date_str][pair_key] = round(rate, 4)

    # Write to CSV in wide format (date, pair1, pair2, ...)
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['date'] + pair_keys
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for date_str in sorted(rate_data.keys()):
            row = {'date': date_str}
            row.update(rate_data[date_str])
            writer.writerow(row)

    total_entries = sum(len(rates) for rates in rate_data.values())
    print(f"\n{'-' * 50}")
    print(f"Exchange rates saved to: {output_file}")
    print(f"Total entries: {total_entries}")
    print(f"Newly fetched: {fetch_count}")
    print(f"Used from cache: {skip_count}")


def main():
    """Main function to fetch and save exchange rate data."""
    print("Exchange Rate Fetcher")
    print("=" * 50)

    # Parse CSV for unique currency pairs
    print("\n1. Scanning my-tickers.csv for currency pairs...")
    currency_pairs, earliest_date = get_currency_pairs('my-tickers.csv')

    if not currency_pairs:
        print("   No currency conversions needed (all transactions in same currency)")
        # Create empty exchange_rates.csv
        with open('exchange_rates.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date'])
        return

    print(f"   Found {len(currency_pairs)} currency pairs:")
    for from_curr, to_curr in currency_pairs:
        print(f"     {from_curr} -> {to_curr}")
    print(f"   Earliest purchase: {earliest_date.strftime('%Y-%m-%d')}")

    # Generate month dates
    print("\n2. Generating monthly dates...")
    today = datetime.now()
    dates = generate_month_dates(earliest_date, today)
    print(f"   Generated {len(dates)} dates from {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")

    # Fetch and save exchange rates
    print("\n3. Fetching exchange rates (skipping existing ones)...")
    fetch_and_save_rates(currency_pairs, dates)

    print("\n" + "=" * 50)
    print("Done! Exchange rates saved to exchange_rates.csv")


if __name__ == '__main__':
    main()

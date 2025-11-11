#!/usr/bin/env python3
"""
Stock Portfolio Visualizer
Parses my-tickers.csv and generates an HTML page with a chart showing
portfolio value at the 1st of each month from earliest purchase to today.
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
                    'purchase_date': purchase_date,
                    'quantity': quantity,
                    'purchase_price': purchase_price,
                    'transaction_fees': transaction_fees
                })

    return transactions


def get_earliest_date(transactions):
    """Get the earliest purchase date from transactions."""
    return min(t['purchase_date'] for t in transactions)


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
        if transaction['purchase_date'] <= target_date:
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


def calculate_portfolio_values(transactions, dates):
    """Calculate portfolio value at each date."""
    portfolio_values = []

    for date in dates:
        holdings = get_holdings_at_date(transactions, date)
        total_value = 0

        print(f"Calculating portfolio value for {date.strftime('%Y-%m-%d')}...")

        for ticker, quantity in holdings.items():
            price = fetch_price(ticker, date)
            if price is not None:
                value = quantity * price
                total_value += value
                print(f"  {ticker}: {quantity} shares × ${price:.2f} = ${value:.2f}")

        portfolio_values.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(total_value, 2)
        })
        print(f"  Total: ${total_value:.2f}\n")

    return portfolio_values


def generate_html(portfolio_values, output_file='portfolio.html'):
    """Generate HTML page with chart visualization."""
    dates = [pv['date'] for pv in portfolio_values]
    values = [pv['value'] for pv in portfolio_values]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Portfolio Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin-top: 30px;
            flex-wrap: wrap;
        }}
        .stat-box {{
            text-align: center;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            min-width: 150px;
            margin: 10px;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .stat-value {{
            color: #333;
            font-size: 24px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stock Portfolio Value Over Time</h1>

        <div class="chart-container">
            <canvas id="portfolioChart"></canvas>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Current Value</div>
                <div class="stat-value">${values[-1]:,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Initial Value</div>
                <div class="stat-value">${values[0]:,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Change</div>
                <div class="stat-value">${values[-1] - values[0]:+,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Percentage Change</div>
                <div class="stat-value">{'N/A' if values[0] == 0 else f'{((values[-1] - values[0]) / values[0] * 100):+.2f}%'}</div>
            </div>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('portfolioChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [{{
                    label: 'Portfolio Value ($)',
                    data: {json.dumps(values)},
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Value: $' + context.parsed.y.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        ticks: {{
                            callback: function(value) {{
                                return '$' + value.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
                            }}
                        }}
                    }},
                    x: {{
                        ticks: {{
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"HTML file generated: {output_file}")


def main():
    """Main function to orchestrate the portfolio visualization."""
    print("Stock Portfolio Visualizer")
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

    # Calculate portfolio values
    print("\n4. Calculating portfolio values...")
    portfolio_values = calculate_portfolio_values(transactions, dates)

    # Generate HTML
    print("\n5. Generating HTML visualization...")
    generate_html(portfolio_values)

    print("\n" + "=" * 50)
    print("Done! Open portfolio.html in your browser to view the chart.")


if __name__ == '__main__':
    main()

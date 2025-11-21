#!/usr/bin/env python3
"""
Portfolio HTML Builder - Step 2
Reads portfolio_data.json and generates an interactive HTML visualization.
"""

import json


def load_portfolio_data(input_file='portfolio_data.json'):
    """Load portfolio data from JSON file."""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        print("Please run 'python fetch_prices.py' first to generate the data file.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        exit(1)


def calculate_cost_basis(transactions, exchange_rates):
    """Calculate total cost basis for each ticker in all three currencies."""
    import json
    cost_basis_usd = {}
    cost_basis_eur = {}
    cost_basis_pln = {}

    # Load exchange rates for conversion (monthly rates for display currencies)
    rates = {}
    try:
        with open('exchange_rates.csv', 'r') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                date = row['date']
                rates[date] = {}
                for key, val in row.items():
                    if key != 'date' and val:
                        rates[date][key] = float(val)
    except:
        pass

    # Get the first available date for fallback conversions
    first_rate_date = min(rates.keys()) if rates else None

    for transaction in transactions:
        ticker = transaction['ticker']
        ticker_currency = transaction.get('ticker_currency', 'USD')
        local_currency = transaction.get('local_currency', 'PLN')
        price_in_local = transaction['price_in_local_currency']
        quantity = transaction['quantity']
        fees_in_local = transaction['fee_in_local_currency']
        exchange_rate = transaction['exchange_rate']  # This is ticker_currency to local_currency

        if ticker not in cost_basis_usd:
            cost_basis_usd[ticker] = 0
            cost_basis_eur[ticker] = 0
            cost_basis_pln[ticker] = 0

        # Cost in local currency (PLN)
        total_cost_pln = (quantity * price_in_local) + fees_in_local

        # Convert to ticker currency using the provided exchange rate
        total_cost_ticker = total_cost_pln / exchange_rate

        # Now convert from ticker currency to all three display currencies
        def convert_from_ticker(value, ticker_curr, to_curr):
            if ticker_curr == to_curr:
                return value
            # Use first available monthly rate for ticker->display conversions
            if first_rate_date:
                pair_key = f"{ticker_curr}_{to_curr}"
                if pair_key in rates[first_rate_date]:
                    return value * rates[first_rate_date][pair_key]
            return value

        if ticker_currency == 'USD':
            cost_usd = total_cost_ticker
            cost_eur = convert_from_ticker(total_cost_ticker, 'USD', 'EUR')
            cost_pln = total_cost_pln
        elif ticker_currency == 'EUR':
            cost_usd = convert_from_ticker(total_cost_ticker, 'EUR', 'USD')
            cost_eur = total_cost_ticker
            cost_pln = total_cost_pln
        else:  # PLN
            cost_usd = convert_from_ticker(total_cost_ticker, 'PLN', 'USD')
            cost_eur = convert_from_ticker(total_cost_ticker, 'PLN', 'EUR')
            cost_pln = total_cost_pln

        cost_basis_usd[ticker] += cost_usd
        cost_basis_eur[ticker] += cost_eur
        cost_basis_pln[ticker] += cost_pln

    return cost_basis_usd, cost_basis_eur, cost_basis_pln


def calculate_cost_basis_over_time(transactions, dates):
    """Calculate cost basis for each ticker at each date in all three currencies."""
    from datetime import datetime
    import csv

    # Load exchange rates (monthly rates)
    rates = {}
    try:
        with open('exchange_rates.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row['date']
                rates[date] = {}
                for key, val in row.items():
                    if key != 'date' and val:
                        rates[date][key] = float(val)
    except:
        pass

    # Get the first available date for fallback conversions
    first_rate_date = min(rates.keys()) if rates else None

    # Convert date strings to datetime for comparison
    date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

    cost_basis_timeline_usd = {}
    cost_basis_timeline_eur = {}
    cost_basis_timeline_pln = {}
    for ticker in set(t['ticker'] for t in transactions):
        cost_basis_timeline_usd[ticker] = []
        cost_basis_timeline_eur[ticker] = []
        cost_basis_timeline_pln[ticker] = []

    def convert_from_ticker(value, ticker_curr, to_curr):
        if ticker_curr == to_curr:
            return value
        # Use first available monthly rate for ticker->display conversions
        if first_rate_date:
            pair_key = f"{ticker_curr}_{to_curr}"
            if pair_key in rates[first_rate_date]:
                return value * rates[first_rate_date][pair_key]
        return value

    # For each date, sum up all transactions that occurred before or on that date
    for date, date_obj in zip(dates, date_objects):
        for ticker in cost_basis_timeline_usd.keys():
            total_cost_usd = 0
            total_cost_eur = 0
            total_cost_pln = 0
            for transaction in transactions:
                if transaction['ticker'] == ticker:
                    trans_date = datetime.strptime(transaction['purchase_date'], '%Y-%m-%d')
                    if trans_date <= date_obj:
                        ticker_currency = transaction.get('ticker_currency', 'USD')
                        price_in_local = transaction['price_in_local_currency']
                        quantity = transaction['quantity']
                        fees_in_local = transaction['fee_in_local_currency']
                        exchange_rate = transaction['exchange_rate']

                        # Cost in local currency (PLN)
                        cost_pln = (quantity * price_in_local) + fees_in_local

                        # Convert to ticker currency using the provided exchange rate
                        cost_ticker = cost_pln / exchange_rate

                        # Convert from ticker currency to all three display currencies
                        if ticker_currency == 'USD':
                            total_cost_usd += cost_ticker
                            total_cost_eur += convert_from_ticker(cost_ticker, 'USD', 'EUR')
                            total_cost_pln += cost_pln
                        elif ticker_currency == 'EUR':
                            total_cost_usd += convert_from_ticker(cost_ticker, 'EUR', 'USD')
                            total_cost_eur += cost_ticker
                            total_cost_pln += cost_pln
                        else:  # PLN
                            total_cost_usd += convert_from_ticker(cost_ticker, 'PLN', 'USD')
                            total_cost_eur += convert_from_ticker(cost_ticker, 'PLN', 'EUR')
                            total_cost_pln += cost_pln

            cost_basis_timeline_usd[ticker].append(total_cost_usd)
            cost_basis_timeline_eur[ticker].append(total_cost_eur)
            cost_basis_timeline_pln[ticker].append(total_cost_pln)

    return cost_basis_timeline_usd, cost_basis_timeline_eur, cost_basis_timeline_pln


def generate_html(data, output_file='portfolio.html'):
    """Generate HTML page with chart visualization from portfolio data."""
    portfolio_values = data['portfolio_values']
    transactions = data['transactions']
    generated_at = data['generated_at']

    dates = [pv['date'] for pv in portfolio_values]
    values_usd = [pv.get('total_value_usd', 0) for pv in portfolio_values]
    values_eur = [pv.get('total_value_eur', 0) for pv in portfolio_values]
    values_pln = [pv.get('total_value_pln', 0) for pv in portfolio_values]

    # Calculate cost basis for each ticker in all three currencies
    cost_basis_usd, cost_basis_eur, cost_basis_pln = calculate_cost_basis(transactions, None)

    # Calculate cost basis over time for profit calculation
    cost_basis_timeline_usd, cost_basis_timeline_eur, cost_basis_timeline_pln = calculate_cost_basis_over_time(transactions, dates)

    # Extract unique tickers and prepare per-ticker data
    all_tickers = set()
    for pv in portfolio_values:
        for holding in pv['holdings']:
            all_tickers.add(holding['ticker'])

    unique_tickers = sorted(list(all_tickers))

    # Color palette for tickers
    colors = [
        'rgb(255, 99, 132)',   # Red
        'rgb(54, 162, 235)',   # Blue
        'rgb(255, 206, 86)',   # Yellow
        'rgb(75, 192, 192)',   # Teal
        'rgb(153, 102, 255)',  # Purple
        'rgb(255, 159, 64)',   # Orange
        'rgb(199, 199, 199)',  # Grey
        'rgb(83, 102, 255)',   # Indigo
        'rgb(255, 99, 255)',   # Pink
        'rgb(99, 255, 132)',   # Green
    ]

    # Build per-ticker datasets (value and profit in all three currencies)
    ticker_datasets = []
    ticker_profit_datasets = []
    for idx, ticker in enumerate(unique_tickers):
        ticker_values_usd = []
        ticker_values_eur = []
        ticker_values_pln = []
        ticker_profits_usd = []
        ticker_profits_eur = []
        ticker_profits_pln = []
        ticker_quantities = []
        for i, pv in enumerate(portfolio_values):
            ticker_value_usd = 0
            ticker_value_eur = 0
            ticker_value_pln = 0
            ticker_quantity = 0
            for holding in pv['holdings']:
                if holding['ticker'] == ticker:
                    ticker_value_usd = holding.get('value_usd', 0)
                    ticker_value_eur = holding.get('value_eur', 0)
                    ticker_value_pln = holding.get('value_pln', 0)
                    ticker_quantity = holding['quantity']
                    break
            ticker_values_usd.append(ticker_value_usd)
            ticker_values_eur.append(ticker_value_eur)
            ticker_values_pln.append(ticker_value_pln)
            ticker_quantities.append(ticker_quantity)

            # Calculate profit at this point in time (all three currencies)
            ticker_cost_usd = cost_basis_timeline_usd[ticker][i]
            ticker_profit_usd = ticker_value_usd - ticker_cost_usd
            ticker_profits_usd.append(ticker_profit_usd)

            ticker_cost_eur = cost_basis_timeline_eur[ticker][i]
            ticker_profit_eur = ticker_value_eur - ticker_cost_eur
            ticker_profits_eur.append(ticker_profit_eur)

            ticker_cost_pln = cost_basis_timeline_pln[ticker][i]
            ticker_profit_pln = ticker_value_pln - ticker_cost_pln
            ticker_profits_pln.append(ticker_profit_pln)

        color = colors[idx % len(colors)]
        color_rgba = color.replace('rgb', 'rgba').replace(')', ', 0.2)')

        # Value dataset (default to PLN)
        ticker_datasets.append({
            'label': ticker,
            'data': ticker_values_pln,
            'dataUSD': ticker_values_usd,
            'dataEUR': ticker_values_eur,
            'dataPLN': ticker_values_pln,
            'borderColor': color,
            'backgroundColor': color_rgba,
            'tension': 0.1,
            'fill': True,
            'tickerName': ticker,
            'quantities': ticker_quantities,
            'profits': ticker_profits_pln,
            'profitsUSD': ticker_profits_usd,
            'profitsEUR': ticker_profits_eur,
            'profitsPLN': ticker_profits_pln
        })

        # Profit dataset (dashed line, same color but darker, default to PLN)
        darker_color = color.replace('rgb', 'rgba').replace(')', ', 0.8)')
        ticker_profit_datasets.append({
            'label': f'{ticker} Profit',
            'data': ticker_profits_pln,
            'dataUSD': ticker_profits_usd,
            'dataEUR': ticker_profits_eur,
            'dataPLN': ticker_profits_pln,
            'borderColor': darker_color,
            'backgroundColor': 'transparent',
            'tension': 0.1,
            'fill': False,
            'borderDash': [5, 5],
            'borderWidth': 2,
            'tickerName': ticker,
            'isProfit': True,
            'hidden': False,
            'order': 2,
            'quantities': ticker_quantities
        })

    # Calculate total profit over time and total quantities (all three currencies)
    total_profit_values_usd = []
    total_profit_values_eur = []
    total_profit_values_pln = []
    total_quantities = []
    for i, pv in enumerate(portfolio_values):
        # Sum up all cost basis at this point in time (USD)
        total_cost_at_date_usd = sum(cost_basis_timeline_usd[ticker][i] for ticker in unique_tickers)
        total_profit_at_date_usd = pv.get('total_value_usd', 0) - total_cost_at_date_usd
        total_profit_values_usd.append(total_profit_at_date_usd)

        # Sum up all cost basis at this point in time (EUR)
        total_cost_at_date_eur = sum(cost_basis_timeline_eur[ticker][i] for ticker in unique_tickers)
        total_profit_at_date_eur = pv.get('total_value_eur', 0) - total_cost_at_date_eur
        total_profit_values_eur.append(total_profit_at_date_eur)

        # Sum up all cost basis at this point in time (PLN)
        total_cost_at_date_pln = sum(cost_basis_timeline_pln[ticker][i] for ticker in unique_tickers)
        total_profit_at_date_pln = pv.get('total_value_pln', 0) - total_cost_at_date_pln
        total_profit_values_pln.append(total_profit_at_date_pln)

        # Sum up all quantities at this point in time
        total_qty = sum(holding['quantity'] for holding in pv['holdings'])
        total_quantities.append(total_qty)

    # Prepare transaction annotations for chart
    # Find the closest chart date for each transaction
    from datetime import datetime
    transaction_annotations = []

    for idx, transaction in enumerate(transactions):
        trans_date = datetime.strptime(transaction['purchase_date'], '%Y-%m-%d')

        # Find the closest date in the chart dates that's >= transaction date
        closest_date = None
        for chart_date in dates:
            chart_date_obj = datetime.strptime(chart_date, '%Y-%m-%d')
            if chart_date_obj >= trans_date:
                closest_date = chart_date
                break

        # If we couldn't find a date >= transaction date, use the first date
        if closest_date is None:
            closest_date = dates[0] if dates else transaction['purchase_date']

        transaction_annotations.append({
            'type': 'line',
            'xMin': closest_date,
            'xMax': closest_date,
            'borderColor': 'rgba(255, 99, 71, 0.5)',
            'borderWidth': 2,
            'borderDash': [5, 5],
            'ticker': transaction['ticker'],
            'label': {
                'display': True,
                'content': f"{transaction['ticker']}: +{transaction['quantity']:.0f}",
                'position': 'start',
                'backgroundColor': 'rgba(255, 99, 71, 0.8)',
                'color': 'white',
                'font': {
                    'size': 10,
                    'weight': 'bold'
                },
                'padding': 4,
                'rotation': 0
            }
        })

    # Calculate statistics for total portfolio (all three currencies)
    current_value_usd = values_usd[-1] if values_usd else 0
    current_value_eur = values_eur[-1] if values_eur else 0
    current_value_pln = values_pln[-1] if values_pln else 0

    # Calculate total cost basis and profit (USD)
    total_cost_basis_usd = sum(cost_basis_usd.values())
    total_profit_usd = current_value_usd - total_cost_basis_usd
    total_profit_percent_usd = ((total_profit_usd / total_cost_basis_usd * 100) if total_cost_basis_usd != 0 else 0)

    # Calculate total cost basis and profit (EUR)
    total_cost_basis_eur = sum(cost_basis_eur.values())
    total_profit_eur = current_value_eur - total_cost_basis_eur
    total_profit_percent_eur = ((total_profit_eur / total_cost_basis_eur * 100) if total_cost_basis_eur != 0 else 0)

    # Calculate total cost basis and profit (PLN)
    total_cost_basis_pln = sum(cost_basis_pln.values())
    total_profit_pln = current_value_pln - total_cost_basis_pln
    total_profit_percent_pln = ((total_profit_pln / total_cost_basis_pln * 100) if total_cost_basis_pln != 0 else 0)

    # Calculate per-ticker statistics (all three currencies)
    ticker_stats = {}
    if portfolio_values:
        current_holdings = portfolio_values[-1]['holdings']
        for holding in current_holdings:
            ticker = holding['ticker']

            # USD
            ticker_cost_usd = cost_basis_usd.get(ticker, 0)
            ticker_value_usd = holding.get('value_usd', 0)
            ticker_profit_usd = ticker_value_usd - ticker_cost_usd
            ticker_return_usd = ((ticker_profit_usd / ticker_cost_usd * 100) if ticker_cost_usd != 0 else 0)

            # EUR
            ticker_cost_eur = cost_basis_eur.get(ticker, 0)
            ticker_value_eur = holding.get('value_eur', 0)
            ticker_profit_eur = ticker_value_eur - ticker_cost_eur
            ticker_return_eur = ((ticker_profit_eur / ticker_cost_eur * 100) if ticker_cost_eur != 0 else 0)

            # PLN
            ticker_cost_pln = cost_basis_pln.get(ticker, 0)
            ticker_value_pln = holding.get('value_pln', 0)
            ticker_profit_pln = ticker_value_pln - ticker_cost_pln
            ticker_return_pln = ((ticker_profit_pln / ticker_cost_pln * 100) if ticker_cost_pln != 0 else 0)

            ticker_stats[ticker] = {
                'current_value_usd': ticker_value_usd,
                'cost_basis_usd': ticker_cost_usd,
                'profit_usd': ticker_profit_usd,
                'return_percent_usd': ticker_return_usd,
                'current_value_eur': ticker_value_eur,
                'cost_basis_eur': ticker_cost_eur,
                'profit_eur': ticker_profit_eur,
                'return_percent_eur': ticker_return_eur,
                'current_value_pln': ticker_value_pln,
                'cost_basis_pln': ticker_cost_pln,
                'profit_pln': ticker_profit_pln,
                'return_percent_pln': ticker_return_pln
            }

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Portfolio Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
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
            margin-bottom: 10px;
        }}
        .generated-info {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }}
        .filter-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
            gap: 10px;
        }}
        .filter-label {{
            font-weight: bold;
            color: #333;
        }}
        .filter-dropdown {{
            padding: 8px 12px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: white;
            font-size: 14px;
            cursor: pointer;
            min-width: 150px;
        }}
        .filter-dropdown:hover {{
            border-color: #007bff;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        .stats-header {{
            text-align: center;
            margin-top: 30px;
            margin-bottom: 10px;
        }}
        .stats-label {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            padding: 8px 16px;
            background-color: #f8f9fa;
            border-radius: 5px;
            display: inline-block;
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
        .stat-value.positive {{
            color: #28a745;
        }}
        .stat-value.negative {{
            color: #dc3545;
        }}
        .holdings-section {{
            margin-top: 40px;
        }}
        .holdings-section h2 {{
            color: #333;
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .ticker {{
            font-weight: bold;
            color: #007bff;
        }}
        td.positive {{
            color: #28a745;
            font-weight: bold;
        }}
        td.negative {{
            color: #dc3545;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stock Portfolio Visualization</h1>
        <div class="generated-info">Data generated: {generated_at}</div>

        <div class="filter-container">
            <label class="filter-label" for="tickerFilter">Select Ticker:</label>
            <select id="tickerFilter" class="filter-dropdown">
                <option value="all">All Tickers</option>
                <option value="total">Total Portfolio Only</option>
"""

    # Add ticker options to dropdown
    for ticker in unique_tickers:
        html_content += f"""                <option value="{ticker}">{ticker}</option>
"""

    html_content += f"""            </select>
            <label class="filter-label" for="currencyFilter">Currency:</label>
            <select id="currencyFilter" class="filter-dropdown">
                <option value="PLN">PLN</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
            </select>
        </div>

        <div class="chart-container">
            <canvas id="portfolioChart"></canvas>
        </div>

        <div class="stats-header">
            <span class="stats-label" id="statsLabel">All Tickers</span>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Current Value</div>
                <div class="stat-value" id="statCurrentValue">{current_value_pln:,.2f} PLN</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Cost</div>
                <div class="stat-value" id="statTotalCost">{total_cost_basis_pln:,.2f} PLN</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Profit/Loss</div>
                <div class="stat-value {'positive' if total_profit_pln >= 0 else 'negative'}" id="statProfit">{total_profit_pln:+,.2f} PLN</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Return</div>
                <div class="stat-value {'positive' if total_profit_percent_pln >= 0 else 'negative'}" id="statReturn">{total_profit_percent_pln:+.2f}%</div>
            </div>
        </div>

        <div class="holdings-section">
            <h2>Current Holdings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Quantity</th>
                        <th>Cost Basis</th>
                        <th>Current Price</th>
                        <th>Current Value</th>
                        <th>Profit/Loss</th>
                        <th>Return %</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add current holdings to table (using PLN as default)
    if portfolio_values:
        current_holdings = portfolio_values[-1]['holdings']
        for holding in current_holdings:
            ticker = holding['ticker']
            ticker_cost_pln = cost_basis_pln.get(ticker, 0)
            ticker_value_pln = holding.get('value_pln', 0)
            ticker_price_pln = holding.get('price_pln', 0)
            ticker_profit_pln = ticker_value_pln - ticker_cost_pln
            ticker_return_pln = ((ticker_profit_pln / ticker_cost_pln * 100) if ticker_cost_pln != 0 else 0)
            profit_class = 'positive' if ticker_profit_pln >= 0 else 'negative'

            html_content += f"""                    <tr>
                        <td class="ticker">{ticker}</td>
                        <td>{holding['quantity']}</td>
                        <td>{ticker_cost_pln:,.2f} PLN</td>
                        <td>{ticker_price_pln:,.2f} PLN</td>
                        <td>{ticker_value_pln:,.2f} PLN</td>
                        <td class="{profit_class}">{ticker_profit_pln:+,.2f} PLN</td>
                        <td class="{profit_class}">{ticker_return_pln:+.2f}%</td>
                    </tr>
"""

    html_content += f"""                </tbody>
            </table>
        </div>

        <div class="holdings-section">
            <h2>Transactions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Purchase Date</th>
                        <th>Quantity</th>
                        <th>Currency</th>
                        <th>Purchase Price</th>
                        <th>Transaction Fees</th>
                        <th>Total Cost (Original)</th>
                        <th>Total Cost (PLN)</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Load exchange rates for transaction cost conversion
    import csv as csv_module
    rates = {}
    try:
        with open('exchange_rates.csv', 'r') as f:
            reader = csv_module.DictReader(f)
            for row in reader:
                date = row['date']
                rates[date] = {}
                for key, val in row.items():
                    if key != 'date' and val:
                        rates[date][key] = float(val)
    except:
        pass

    def convert_to_pln(value, from_curr, date):
        if from_curr == 'PLN':
            return value
        pair_key = f"{from_curr}_PLN"
        if date in rates and pair_key in rates[date]:
            return value * rates[date][pair_key]
        return value

    # Add transactions to table
    for transaction in transactions:
        ticker_currency = transaction.get('ticker_currency', 'USD')
        local_currency = transaction.get('local_currency', 'PLN')
        purchase_date = transaction['purchase_date']
        quantity = transaction['quantity']
        price_in_local = transaction['price_in_local_currency']
        fee_in_local = transaction['fee_in_local_currency']
        exchange_rate = transaction['exchange_rate']

        # Calculate costs
        total_cost_pln = (quantity * price_in_local) + fee_in_local
        # Calculate price and fee in ticker currency using the exchange rate
        price_in_ticker = price_in_local / exchange_rate
        fee_in_ticker = fee_in_local / exchange_rate
        total_cost_ticker = (quantity * price_in_ticker) + fee_in_ticker

        html_content += f"""                    <tr>
                        <td class="ticker">{transaction['ticker']}</td>
                        <td>{purchase_date}</td>
                        <td>{quantity}</td>
                        <td><strong>{ticker_currency}</strong></td>
                        <td>{price_in_ticker:,.2f} {ticker_currency}</td>
                        <td>{fee_in_ticker:,.2f} {ticker_currency}</td>
                        <td>{total_cost_ticker:,.2f} {ticker_currency}</td>
                        <td>{total_cost_pln:,.2f} PLN</td>
                    </tr>
"""

    html_content += f"""                </tbody>
            </table>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('portfolioChart').getContext('2d');

        // Currency settings (must be declared before chart creation)
        let currentCurrency = 'PLN';

        // Ticker value datasets
        const tickerValueDatasets = {json.dumps(ticker_datasets)};

        // Ticker profit datasets
        const tickerProfitDatasets = {json.dumps(ticker_profit_datasets)};

        // Total portfolio value dataset
        const totalValueDataset = {{
            label: 'Total Portfolio',
            data: {json.dumps(values_pln)},
            dataUSD: {json.dumps(values_usd)},
            dataEUR: {json.dumps(values_eur)},
            dataPLN: {json.dumps(values_pln)},
            borderColor: 'rgb(0, 0, 0)',
            backgroundColor: 'rgba(0, 0, 0, 0.1)',
            tension: 0.1,
            fill: true,
            borderWidth: 3,
            tickerName: 'total',
            quantities: {json.dumps(total_quantities)},
            profits: {json.dumps(total_profit_values_pln)},
            profitsUSD: {json.dumps(total_profit_values_usd)},
            profitsEUR: {json.dumps(total_profit_values_eur)},
            profitsPLN: {json.dumps(total_profit_values_pln)}
        }};

        // Total portfolio profit dataset
        const totalProfitDataset = {{
            label: 'Total Portfolio Profit',
            data: {json.dumps(total_profit_values_pln)},
            dataUSD: {json.dumps(total_profit_values_usd)},
            dataEUR: {json.dumps(total_profit_values_eur)},
            dataPLN: {json.dumps(total_profit_values_pln)},
            borderColor: 'rgba(0, 0, 0, 0.8)',
            backgroundColor: 'transparent',
            tension: 0.1,
            fill: false,
            borderDash: [5, 5],
            borderWidth: 3,
            tickerName: 'total',
            isProfit: true,
            hidden: false,
            order: 2,
            quantities: {json.dumps(total_quantities)}
        }};

        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [...tickerValueDatasets, ...tickerProfitDatasets, totalValueDataset, totalProfitDataset]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            filter: function(item) {{
                                // Only show value datasets in legend, not profit datasets
                                return !item.text.includes('Profit');
                            }}
                        }},
                        onClick: function(e, legendItem, legend) {{
                            const index = legendItem.datasetIndex;
                            const ci = legend.chart;
                            const dataset = ci.data.datasets[index];

                            // Skip if this is a profit dataset (shouldn't happen but safety check)
                            if (dataset.isProfit) return;

                            const tickerName = dataset.tickerName;

                            // Find both value and profit datasets for this ticker
                            ci.data.datasets.forEach((ds, i) => {{
                                if (ds.tickerName === tickerName) {{
                                    const meta = ci.getDatasetMeta(i);
                                    meta.hidden = meta.hidden === null ? !ci.data.datasets[i].hidden : null;
                                }}
                            }});

                            ci.update();
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const dataset = context.dataset;
                                const dataIndex = context.dataIndex;
                                const value = context.parsed.y;
                                const currency = currentCurrency;
                                const formattedValue = value.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',') + ' ' + currency;

                                let lines = [];

                                if (dataset.isProfit) {{
                                    // Profit dataset - show profit and quantity
                                    lines.push(dataset.label + ': ' + formattedValue);
                                    if (dataset.quantities && dataset.quantities[dataIndex]) {{
                                        lines.push('  Shares: ' + dataset.quantities[dataIndex].toFixed(1));
                                    }}
                                }} else {{
                                    // Value dataset - show value, quantity, and profit
                                    lines.push(dataset.label + ': ' + formattedValue);
                                    if (dataset.quantities && dataset.quantities[dataIndex]) {{
                                        lines.push('  Shares: ' + dataset.quantities[dataIndex].toFixed(1));
                                    }}
                                    if (dataset.profits && dataset.profits[dataIndex] !== undefined) {{
                                        const profit = dataset.profits[dataIndex];
                                        const profitSign = profit >= 0 ? '+' : '';
                                        const formattedProfit = profitSign + profit.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',') + ' ' + currency;
                                        lines.push('  Profit: ' + formattedProfit);
                                    }}
                                }}

                                return lines;
                            }}
                        }}
                    }},
                    annotation: {{
                        annotations: {json.dumps(transaction_annotations)}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        ticks: {{
                            callback: function(value) {{
                                const currency = currentCurrency;
                                return value.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',') + ' ' + currency;
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

        // Store all annotations
        const allAnnotations = {json.dumps(transaction_annotations)};

        // Store ticker statistics (all three currencies)
        const tickerStats = {json.dumps(ticker_stats)};
        const totalStats = {{
            current_value_usd: {current_value_usd},
            cost_basis_usd: {total_cost_basis_usd},
            profit_usd: {total_profit_usd},
            return_percent_usd: {total_profit_percent_usd},
            current_value_eur: {current_value_eur},
            cost_basis_eur: {total_cost_basis_eur},
            profit_eur: {total_profit_eur},
            return_percent_eur: {total_profit_percent_eur},
            current_value_pln: {current_value_pln},
            cost_basis_pln: {total_cost_basis_pln},
            profit_pln: {total_profit_pln},
            return_percent_pln: {total_profit_percent_pln}
        }};

        // Function to update stats display
        function updateStats(label, stats) {{
            const currency = currentCurrency;
            const suffix = ' ' + currency;

            const currentValue = stats['current_value_' + currency.toLowerCase()];
            const costBasis = stats['cost_basis_' + currency.toLowerCase()];
            const profit = stats['profit_' + currency.toLowerCase()];
            const returnPercent = stats['return_percent_' + currency.toLowerCase()];

            document.getElementById('statsLabel').textContent = label;
            document.getElementById('statCurrentValue').textContent = currentValue.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',') + suffix;
            document.getElementById('statTotalCost').textContent = costBasis.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',') + suffix;

            const profitElement = document.getElementById('statProfit');
            const profitSign = profit >= 0 ? '+' : '';
            profitElement.textContent = profitSign + profit.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',') + suffix;
            profitElement.className = 'stat-value ' + (profit >= 0 ? 'positive' : 'negative');

            const returnElement = document.getElementById('statReturn');
            const returnSign = returnPercent >= 0 ? '+' : '';
            returnElement.textContent = returnSign + returnPercent.toFixed(2) + '%';
            returnElement.className = 'stat-value ' + (returnPercent >= 0 ? 'positive' : 'negative');
        }}

        // Function to switch dataset currency
        function switchCurrency(currency) {{
            currentCurrency = currency;
            const dataKey = 'data' + currency;
            const profitKey = 'profits' + currency;

            // Update all datasets
            chart.data.datasets.forEach(dataset => {{
                if (dataset[dataKey]) {{
                    dataset.data = dataset[dataKey];
                }}
                if (dataset[profitKey]) {{
                    dataset.profits = dataset[profitKey];
                }}
            }});

            chart.update();

            // Update stats based on current filter
            const selectedTicker = document.getElementById('tickerFilter').value;
            if (selectedTicker === 'all' || selectedTicker === 'total') {{
                updateStats(selectedTicker === 'all' ? 'All Tickers' : 'Total Portfolio Only', totalStats);
            }} else {{
                updateStats(selectedTicker, tickerStats[selectedTicker]);
            }}
        }}

        // Dropdown filter functionality
        document.getElementById('tickerFilter').addEventListener('change', function(e) {{
            const selectedTicker = e.target.value;

            if (selectedTicker === 'all') {{
                // Show all datasets (ticker values, ticker profits, total value, and total profit)
                chart.data.datasets = [...tickerValueDatasets, ...tickerProfitDatasets, totalValueDataset, totalProfitDataset];
                // Show all annotations
                chart.options.plugins.annotation.annotations = allAnnotations;
                // Update stats to show total portfolio
                updateStats('All Tickers', totalStats);
            }} else if (selectedTicker === 'total') {{
                // Show only total portfolio value and profit
                chart.data.datasets = [totalValueDataset, totalProfitDataset];
                // Show all annotations for total view
                chart.options.plugins.annotation.annotations = allAnnotations;
                // Update stats to show total portfolio
                updateStats('Total Portfolio Only', totalStats);
            }} else {{
                // Show only the selected ticker's value and profit
                const tickerValueDs = tickerValueDatasets.filter(ds => ds.tickerName === selectedTicker);
                const tickerProfitDs = tickerProfitDatasets.filter(ds => ds.tickerName === selectedTicker);
                chart.data.datasets = [...tickerValueDs, ...tickerProfitDs];
                // Show only annotations for selected ticker
                chart.options.plugins.annotation.annotations = allAnnotations.filter(ann => ann.ticker === selectedTicker);
                // Update stats to show selected ticker
                updateStats(selectedTicker, tickerStats[selectedTicker]);
            }}

            chart.update();
        }});

        // Currency filter functionality
        document.getElementById('currencyFilter').addEventListener('change', function(e) {{
            const selectedCurrency = e.target.value;
            switchCurrency(selectedCurrency);
        }});

    </script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"HTML file generated: {output_file}")


def main():
    """Main function to build HTML visualization."""
    print("Portfolio HTML Builder - Step 2")
    print("=" * 50)

    # Load portfolio data
    print("\n1. Loading portfolio data from JSON...")
    data = load_portfolio_data()
    print(f"   Loaded {len(data['portfolio_values'])} data points")
    print(f"   Data generated at: {data['generated_at']}")

    # Generate HTML
    print("\n2. Generating HTML visualization...")
    generate_html(data)

    print("\n" + "=" * 50)
    print("Done! Open portfolio.html in your browser to view the chart.")


if __name__ == '__main__':
    main()

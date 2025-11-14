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


def calculate_cost_basis(transactions):
    """Calculate total cost basis for each ticker."""
    cost_basis = {}
    for transaction in transactions:
        ticker = transaction['ticker']
        total_cost = (transaction['quantity'] * transaction['purchase_price']) + transaction['transaction_fees']

        if ticker not in cost_basis:
            cost_basis[ticker] = 0
        cost_basis[ticker] += total_cost

    return cost_basis


def calculate_cost_basis_over_time(transactions, dates):
    """Calculate cost basis for each ticker at each date."""
    from datetime import datetime

    # Convert date strings to datetime for comparison
    date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

    cost_basis_timeline = {}
    for ticker in set(t['ticker'] for t in transactions):
        cost_basis_timeline[ticker] = []

    # For each date, sum up all transactions that occurred before or on that date
    for date, date_obj in zip(dates, date_objects):
        for ticker in cost_basis_timeline.keys():
            total_cost = 0
            for transaction in transactions:
                if transaction['ticker'] == ticker:
                    trans_date = datetime.strptime(transaction['purchase_date'], '%Y-%m-%d')
                    if trans_date <= date_obj:
                        total_cost += (transaction['quantity'] * transaction['purchase_price']) + transaction['transaction_fees']
            cost_basis_timeline[ticker].append(total_cost)

    return cost_basis_timeline


def generate_html(data, output_file='portfolio.html'):
    """Generate HTML page with chart visualization from portfolio data."""
    portfolio_values = data['portfolio_values']
    transactions = data['transactions']
    generated_at = data['generated_at']

    dates = [pv['date'] for pv in portfolio_values]
    values = [pv['total_value'] for pv in portfolio_values]

    # Calculate cost basis for each ticker
    cost_basis = calculate_cost_basis(transactions)

    # Calculate cost basis over time for profit calculation
    cost_basis_timeline = calculate_cost_basis_over_time(transactions, dates)

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

    # Build per-ticker datasets (both value and profit)
    ticker_datasets = []
    ticker_profit_datasets = []
    for idx, ticker in enumerate(unique_tickers):
        ticker_values = []
        ticker_profits = []
        ticker_quantities = []
        for i, pv in enumerate(portfolio_values):
            ticker_value = 0
            ticker_quantity = 0
            for holding in pv['holdings']:
                if holding['ticker'] == ticker:
                    ticker_value = holding['value']
                    ticker_quantity = holding['quantity']
                    break
            ticker_values.append(ticker_value)
            ticker_quantities.append(ticker_quantity)

            # Calculate profit at this point in time
            ticker_cost = cost_basis_timeline[ticker][i]
            ticker_profit = ticker_value - ticker_cost
            ticker_profits.append(ticker_profit)

        color = colors[idx % len(colors)]
        color_rgba = color.replace('rgb', 'rgba').replace(')', ', 0.2)')

        # Value dataset
        ticker_datasets.append({
            'label': ticker,
            'data': ticker_values,
            'borderColor': color,
            'backgroundColor': color_rgba,
            'tension': 0.1,
            'fill': True,
            'tickerName': ticker,
            'quantities': ticker_quantities,
            'profits': ticker_profits
        })

        # Profit dataset (dashed line, same color but darker)
        darker_color = color.replace('rgb', 'rgba').replace(')', ', 0.8)')
        ticker_profit_datasets.append({
            'label': f'{ticker} Profit',
            'data': ticker_profits,
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

    # Calculate total profit over time and total quantities
    total_profit_values = []
    total_quantities = []
    for i, pv in enumerate(portfolio_values):
        # Sum up all cost basis at this point in time
        total_cost_at_date = sum(cost_basis_timeline[ticker][i] for ticker in unique_tickers)
        total_profit_at_date = pv['total_value'] - total_cost_at_date
        total_profit_values.append(total_profit_at_date)

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

    # Calculate statistics for total portfolio
    current_value = values[-1] if values else 0
    initial_value = values[0] if values else 0
    total_change = current_value - initial_value
    percent_change = ((total_change / initial_value * 100) if initial_value != 0 else 0)

    # Calculate total cost basis and profit
    total_cost_basis = sum(cost_basis.values())
    total_profit = current_value - total_cost_basis
    total_profit_percent = ((total_profit / total_cost_basis * 100) if total_cost_basis != 0 else 0)

    # Calculate per-ticker statistics
    ticker_stats = {}
    if portfolio_values:
        current_holdings = portfolio_values[-1]['holdings']
        for holding in current_holdings:
            ticker = holding['ticker']
            ticker_cost = cost_basis.get(ticker, 0)
            ticker_value = holding['value']
            ticker_profit = ticker_value - ticker_cost
            ticker_return = ((ticker_profit / ticker_cost * 100) if ticker_cost != 0 else 0)

            ticker_stats[ticker] = {
                'current_value': ticker_value,
                'cost_basis': ticker_cost,
                'profit': ticker_profit,
                'return_percent': ticker_return
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
                <div class="stat-value" id="statCurrentValue">${current_value:,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Cost</div>
                <div class="stat-value" id="statTotalCost">${total_cost_basis:,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Profit/Loss</div>
                <div class="stat-value {'positive' if total_profit >= 0 else 'negative'}" id="statProfit">${total_profit:+,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Return</div>
                <div class="stat-value {'positive' if total_profit_percent >= 0 else 'negative'}" id="statReturn">{total_profit_percent:+.2f}%</div>
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

    # Add current holdings to table
    if portfolio_values:
        current_holdings = portfolio_values[-1]['holdings']
        for holding in current_holdings:
            ticker = holding['ticker']
            ticker_cost = cost_basis.get(ticker, 0)
            ticker_profit = holding['value'] - ticker_cost
            ticker_return = ((ticker_profit / ticker_cost * 100) if ticker_cost != 0 else 0)
            profit_class = 'positive' if ticker_profit >= 0 else 'negative'

            html_content += f"""                    <tr>
                        <td class="ticker">{ticker}</td>
                        <td>{holding['quantity']}</td>
                        <td>${ticker_cost:,.2f}</td>
                        <td>${holding['price']:,.2f}</td>
                        <td>${holding['value']:,.2f}</td>
                        <td class="{profit_class}">${ticker_profit:+,.2f}</td>
                        <td class="{profit_class}">{ticker_return:+.2f}%</td>
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
                        <th>Purchase Price</th>
                        <th>Transaction Fees</th>
                        <th>Total Cost</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add transactions to table
    for transaction in transactions:
        total_cost = (transaction['quantity'] * transaction['purchase_price']) + transaction['transaction_fees']
        html_content += f"""                    <tr>
                        <td class="ticker">{transaction['ticker']}</td>
                        <td>{transaction['purchase_date']}</td>
                        <td>{transaction['quantity']}</td>
                        <td>${transaction['purchase_price']:,.2f}</td>
                        <td>${transaction['transaction_fees']:,.2f}</td>
                        <td>${total_cost:,.2f}</td>
                    </tr>
"""

    html_content += f"""                </tbody>
            </table>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('portfolioChart').getContext('2d');

        // Ticker value datasets
        const tickerValueDatasets = {json.dumps(ticker_datasets)};

        // Ticker profit datasets
        const tickerProfitDatasets = {json.dumps(ticker_profit_datasets)};

        // Total portfolio value dataset
        const totalValueDataset = {{
            label: 'Total Portfolio',
            data: {json.dumps(values)},
            borderColor: 'rgb(0, 0, 0)',
            backgroundColor: 'rgba(0, 0, 0, 0.1)',
            tension: 0.1,
            fill: true,
            borderWidth: 3,
            tickerName: 'total',
            quantities: {json.dumps(total_quantities)},
            profits: {json.dumps(total_profit_values)}
        }};

        // Total portfolio profit dataset
        const totalProfitDataset = {{
            label: 'Total Portfolio Profit',
            data: {json.dumps(total_profit_values)},
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
                                const formattedValue = '$' + value.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');

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
                                        const formattedProfit = '$' + profitSign + profit.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
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

        // Store all annotations
        const allAnnotations = {json.dumps(transaction_annotations)};

        // Store ticker statistics
        const tickerStats = {json.dumps(ticker_stats)};
        const totalStats = {{
            current_value: {current_value},
            cost_basis: {total_cost_basis},
            profit: {total_profit},
            return_percent: {total_profit_percent}
        }};

        // Function to update stats display
        function updateStats(label, stats) {{
            document.getElementById('statsLabel').textContent = label;
            document.getElementById('statCurrentValue').textContent = '$' + stats.current_value.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            document.getElementById('statTotalCost').textContent = '$' + stats.cost_basis.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');

            const profitElement = document.getElementById('statProfit');
            const profitSign = stats.profit >= 0 ? '+' : '';
            profitElement.textContent = '$' + profitSign + stats.profit.toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            profitElement.className = 'stat-value ' + (stats.profit >= 0 ? 'positive' : 'negative');

            const returnElement = document.getElementById('statReturn');
            const returnSign = stats.return_percent >= 0 ? '+' : '';
            returnElement.textContent = returnSign + stats.return_percent.toFixed(2) + '%';
            returnElement.className = 'stat-value ' + (stats.return_percent >= 0 ? 'positive' : 'negative');
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

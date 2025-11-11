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


def generate_html(data, output_file='portfolio.html'):
    """Generate HTML page with chart visualization from portfolio data."""
    portfolio_values = data['portfolio_values']
    transactions = data['transactions']
    generated_at = data['generated_at']

    dates = [pv['date'] for pv in portfolio_values]
    values = [pv['total_value'] for pv in portfolio_values]

    # Calculate statistics
    current_value = values[-1] if values else 0
    initial_value = values[0] if values else 0
    total_change = current_value - initial_value
    percent_change = ((total_change / initial_value * 100) if initial_value != 0 else 0)

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
            margin-bottom: 10px;
        }}
        .generated-info {{
            text-align: center;
            color: #666;
            font-size: 14px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Stock Portfolio Visualization</h1>
        <div class="generated-info">Data generated: {generated_at}</div>

        <div class="chart-container">
            <canvas id="portfolioChart"></canvas>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Current Value</div>
                <div class="stat-value">${current_value:,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Initial Value</div>
                <div class="stat-value">${initial_value:,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Change</div>
                <div class="stat-value {'positive' if total_change >= 0 else 'negative'}">${total_change:+,.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Percentage Change</div>
                <div class="stat-value {'positive' if percent_change >= 0 else 'negative'}">{'N/A' if initial_value == 0 else f'{percent_change:+.2f}%'}</div>
            </div>
        </div>

        <div class="holdings-section">
            <h2>Current Holdings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Quantity</th>
                        <th>Current Price</th>
                        <th>Current Value</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add current holdings to table
    if portfolio_values:
        current_holdings = portfolio_values[-1]['holdings']
        for holding in current_holdings:
            html_content += f"""                    <tr>
                        <td class="ticker">{holding['ticker']}</td>
                        <td>{holding['quantity']}</td>
                        <td>${holding['price']:,.2f}</td>
                        <td>${holding['value']:,.2f}</td>
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

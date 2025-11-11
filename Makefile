.PHONY: help install fetch build open clean view-csv view-data test-ticker run

help:
	@echo "Available commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make fetch        - [Step 1] Fetch prices and generate portfolio_data.json"
	@echo "  make build        - [Step 2] Build portfolio.html from portfolio_data.json"
	@echo "  make run          - Run both steps and open portfolio in browser"
	@echo "  make open         - Open portfolio.html in browser"
	@echo "  make view-csv     - Display contents of my-tickers.csv"
	@echo "  make view-data    - Display portfolio_data.json"
	@echo "  make test-ticker  - Test fetching price for a ticker symbol"
	@echo "  make clean        - Remove generated files"
	@echo "  make help         - Show this help message"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

fetch:
	@echo "[Step 1] Fetching prices and generating data file..."
	python fetch_prices.py
	@echo "✓ Data fetched and saved to portfolio_data.json"

build:
	@echo "[Step 2] Building HTML visualization..."
	python build_html.py
	@echo "✓ HTML generated"

open:
	@echo "Opening portfolio.html..."
	open portfolio.html

run: fetch build open

view-csv:
	@echo "Contents of my-tickers.csv:"
	@cat my-tickers.csv

view-data:
	@echo "Portfolio data (portfolio_data.json):"
	@if [ -f portfolio_data.json ]; then \
		cat portfolio_data.json | python -m json.tool; \
	else \
		echo "Error: portfolio_data.json not found. Run 'make fetch' first."; \
	fi

test-ticker:
	@echo "Enter ticker symbol to test (e.g., VHVE.L, AAPL):"
	@read ticker; \
	python -c "import yfinance as yf; from datetime import datetime; \
	stock = yf.Ticker('$$ticker'); \
	hist = stock.history(period='5d'); \
	print('\nLast 5 days of prices:'); \
	print(hist[['Close']]) if not hist.empty else print('No data found for $$ticker')"

clean:
	@echo "Removing generated files..."
	rm -f portfolio.html portfolio_data.json
	@echo "✓ Cleaned"

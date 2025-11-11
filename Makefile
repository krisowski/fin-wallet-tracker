.PHONY: help install fetch build open clean view-csv view-prices view-data test-ticker run

help:
	@echo "Available commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make fetch        - [Step 1] Fetch prices from Yahoo and save to prices.csv"
	@echo "  make build        - [Step 2] Prepare portfolio_data.json and build portfolio.html"
	@echo "  make run          - Run both steps and open portfolio in browser"
	@echo "  make open         - Open portfolio.html in browser"
	@echo "  make view-csv     - Display contents of my-tickers.csv"
	@echo "  make view-prices  - Display contents of prices.csv"
	@echo "  make view-data    - Display portfolio_data.json"
	@echo "  make test-ticker  - Test fetching price for a ticker symbol"
	@echo "  make clean        - Remove generated files"
	@echo "  make help         - Show this help message"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

fetch:
	@echo "[Step 1] Fetching prices from Yahoo Finance..."
	python fetch_prices.py
	@echo "✓ Prices fetched and saved to prices.csv"

build:
	@echo "[Step 2] Preparing portfolio data and building HTML..."
	python prepare_data.py
	python build_html.py
	@echo "✓ Portfolio data prepared and HTML generated"

open:
	@echo "Opening portfolio.html..."
	open portfolio.html

run: fetch build open

view-csv:
	@echo "Contents of my-tickers.csv:"
	@cat my-tickers.csv

view-prices:
	@echo "Contents of prices.csv:"
	@if [ -f prices.csv ]; then \
		cat prices.csv; \
	else \
		echo "Error: prices.csv not found. Run 'make fetch' first."; \
	fi

view-data:
	@echo "Portfolio data (portfolio_data.json):"
	@if [ -f portfolio_data.json ]; then \
		cat portfolio_data.json | python -m json.tool; \
	else \
		echo "Error: portfolio_data.json not found. Run 'make build' first."; \
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
	rm -f portfolio.html portfolio_data.json prices.csv
	@echo "✓ Cleaned"

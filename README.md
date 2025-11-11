# fin-wallet-tracker

A simple Python-based portfolio tracker that visualizes stock holdings over time.

## Overview

This tool parses a CSV file containing stock purchase transactions and generates an interactive HTML chart showing your portfolio's value at the beginning of each month from your earliest purchase to today. Historical prices are automatically fetched from Yahoo Finance.

## Quick Start

```bash
make install    # Install dependencies
make run        # Generate and view portfolio
```

Add your transactions to `my-tickers.csv` and run `make run` to see your portfolio growth!

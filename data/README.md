# Data Sources

## Overview

This directory contains financial time-series data used by the Agentic Financial Risk Assistant.

The current version ships with **synthetic sample data** that reproduces realistic statistical properties (trend, volatility clustering, drawdown events) of the real assets. This ensures the project is fully reproducible without requiring external downloads or API keys.

Real data can be substituted at any time using the download instructions below. The data loading and validation pipeline is identical for both synthetic and real data.

---

## Datasets

### 1. Equinor ASA (EQNR), Norwegian oil and gas company

| Field | Value |
|---|---|
| File | `data/raw/equinor_stock_sample.csv` |
| Ticker | EQNR (NYSE) / EQNR.OL (Oslo Stock Exchange) |
| Period | 2018-01-01 to 2024-12-31 |
| Columns | `Date`, `Close` |
| Frequency | Daily (business days) |
| Currency | USD (NYSE listing) |
| Source | Synthetic sample (real: Yahoo Finance) |
| Status | Bundled with repository |

### 2. Brent crude oil

| Field | Value |
|---|---|
| File | `data/raw/brent_crude_sample.csv` |
| Ticker | BZ=F (Yahoo Finance) |
| Period | 2018-01-01 to 2024-12-31 |
| Columns | `Date`, `Close` |
| Frequency | Daily (business days) |
| Currency | USD per barrel |
| Source | Synthetic sample (real: Yahoo Finance) |
| Status | Bundled with repository |

### 3. USD/NOK exchange rate

| Field | Value |
|---|---|
| File | `data/raw/usd_nok_sample.csv` |
| Ticker | USDNOK=X (Yahoo Finance) / USDNOK (Stooq) |
| Period | 2018-01-01 to 2024-12-31 |
| Columns | `Date`, `Close` |
| Frequency | Daily (business days) |
| Currency | NOK per 1 USD |
| Source | Synthetic sample (real: Yahoo Finance or Stooq) |
| Status | Bundled with repository |

### 4. S&P 500 index

| Field | Value |
|---|---|
| File | `data/raw/sp500_sample.csv` |
| Ticker | ^GSPC (Yahoo Finance) |
| Period | 2018-01-01 to 2024-12-31 |
| Columns | `Date`, `Close` |
| Frequency | Daily (business days) |
| Currency | Index points (USD-denominated) |
| Source | Synthetic sample (real: Yahoo Finance) |
| Status | Bundled with repository |

### 5. VIX volatility index

| Field | Value |
|---|---|
| File | `data/raw/vix_sample.csv` |
| Ticker | ^VIX (Yahoo Finance) |
| Period | 2018-01-01 to 2024-12-31 |
| Columns | `Date`, `Close` |
| Frequency | Daily (business days) |
| Currency | Volatility index (percentage points) |
| Source | Synthetic sample (real: Yahoo Finance) |
| Status | Bundled with repository |

---

## Downloading real data

To replace synthetic samples with real market data, use `yfinance`:

```bash
pip install yfinance
```

```python
import yfinance as yf

tickers = {
    "equinor_stock": "EQNR",
    "brent_crude": "BZ=F",
    "usd_nok": "USDNOK=X",
    "sp500": "^GSPC",
    "vix": "^VIX",
}

for name, ticker in tickers.items():
    df = yf.download(ticker, start="2018-01-01", end="2024-12-31")
    df[["Close"]].to_csv(f"data/raw/{name}_sample.csv")
```

> Note: `BZ=F` has limited history on Yahoo Finance. Alternative: download Brent from the U.S. Energy Information Administration (EIA) at eia.gov.

---

## Data cleaning steps applied to synthetic samples

1. Business days only (weekends and holidays excluded)
2. Date column parsed as `datetime` and set as index
3. No missing values in the `Close` column
4. All prices are strictly positive
5. Column renamed to `Close` for consistency across all datasets

---

## Data directory structure

```
data/
├── raw/                  # Source files (synthetic or downloaded)
│   ├── equinor_stock_sample.csv
│   ├── brent_crude_sample.csv
│   ├── usd_nok_sample.csv
│   ├── sp500_sample.csv
│   └── vix_sample.csv
├── processed/            # Cleaned outputs (generated at runtime)
└── README.md             # This file
```

---

## Important notes

- Do not commit real downloaded data files to the repository if they are large or have restrictive redistribution terms.
- The synthetic samples are generated with a fixed random seed (42) for full reproducibility.
- All synthetic samples are designed to pass the data validation pipeline in `src/data/validators.py`.
- This file is included in the RAG source set so the agent can answer questions about data provenance.

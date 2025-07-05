# Project Log

## Current phase
Phase 2 — Core financial risk engine — COMPLETE

## Current status
- Completed:
  - Phase 1: full project skeleton, synthetic CSVs, tracker files (see previous entry)
  - Phase 2:
    - src/data/loaders.py — CSV loader with date parsing, column validation, sort, missing-value handling
    - src/data/validators.py — validate() and assert_valid() with 5 checks (columns, dtype, missing, negative, min obs)
    - src/risk/returns.py — simple_returns, log_returns, cumulative_returns
    - src/risk/volatility.py — daily_volatility, annualised_volatility, rolling_volatility
    - src/risk/drawdown.py — wealth_index, running_maximum, drawdown_series, max_drawdown, max_drawdown_date
    - src/risk/var.py — historical_var, parametric_var, expected_shortfall (scipy.stats)
    - src/risk/rolling.py — rolling_mean_return, rolling_volatility, rolling_var, stress_period_flag
    - app/components/charts.py — Plotly chart builders: price, returns, rolling vol, drawdown, VaR
    - tests/test_returns.py — 8 tests, all pass
    - tests/test_volatility.py — 6 tests, all pass
    - tests/test_drawdown.py — 7 tests, all pass
    - tests/test_var.py — 7 tests, all pass
    - tests/test_data_validation.py — 11 tests, all pass
    - 39/39 tests passing
- In progress: nothing
- Blocked: nothing

## Files created
- src/data/loaders.py
- src/data/validators.py
- src/risk/returns.py
- src/risk/volatility.py
- src/risk/drawdown.py
- src/risk/var.py
- src/risk/rolling.py
- app/components/charts.py
- tests/test_returns.py
- tests/test_volatility.py
- tests/test_drawdown.py
- tests/test_var.py
- tests/test_data_validation.py

## Files modified
- src/data/loaders.py — removed deprecated infer_datetime_format argument
- tests/test_volatility.py — corrected rolling_volatility length assertion (len-1 because log_returns drops first row)

## Commands run
- .venv\Scripts\pip install scipy==1.13.1 pytest==8.3.5
- .venv\Scripts\pytest tests/test_returns.py tests/test_volatility.py tests/test_drawdown.py tests/test_var.py tests/test_data_validation.py -v
  → 39 passed in 1.41s

## Errors / issues
- test_rolling_volatility_length: asserted len(rv)==len(prices) but rolling_volatility calls log_returns which drops 1 row. Fixed test assertion to len(prices)-1.
- infer_datetime_format deprecation warning in loaders.py — removed the argument (default behaviour is correct in pandas 2.2).

## Decisions made
- scipy==1.13.1 added to requirements.txt for parametric VaR (stats.norm.ppf)
- rolling_volatility in src/risk/rolling.py is a standalone function (does not re-export from volatility.py) to keep rolling module self-contained

## Next exact task
Phase 3 — Streamlit app interface
Build app/streamlit_app.py, app/components/sidebar.py, app/components/risk_summary.py

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.

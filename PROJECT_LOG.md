# Project Log

## Current phase
Phase 1 — Project setup, data source, and scope locking — COMPLETE

## Current status
- Completed:
  - Private GitHub repository created (eigenreza/agentic-financial-risk-assistant)
  - Git initialized and remote added
  - Full directory structure created
  - .gitignore, LICENSE, pyproject.toml, requirements.txt created
  - README.md written (project overview, architecture, quickstart, responsible AI section)
  - data/README.md written (all five datasets documented, real download instructions included)
  - src/data/sample_data.py written (GBM-based synthetic data generator, fixed seed 42)
  - All five synthetic CSVs generated: equinor, brent_crude, usd_nok, sp500, vix
  - Python 3.11 virtual environment created (.venv)
  - pandas==2.2.3 and numpy==1.26.4 installed and verified
  - __init__.py files created for all packages
- In progress: nothing
- Blocked: nothing

## Files created
- .gitignore
- LICENSE
- pyproject.toml
- requirements.txt
- README.md
- data/README.md
- src/data/sample_data.py
- data/raw/equinor_stock_sample.csv (synthetic, ~55 KB)
- data/raw/brent_crude_sample.csv (synthetic, ~55 KB)
- data/raw/usd_nok_sample.csv (synthetic, ~55 KB)
- data/raw/sp500_sample.csv (synthetic, ~55 KB)
- data/raw/vix_sample.csv (synthetic, ~55 KB)
- __init__.py in all src/* and app/* packages
- PROJECT_LOG.md (this file)
- TODO.md

## Files modified
None (first commit)

## Commands run
- winget install GitHub.cli --source winget --accept-source-agreements --accept-package-agreements
- gh repo create agentic-financial-risk-assistant --private ...
- git init
- git remote add origin https://github.com/eigenreza/agentic-financial-risk-assistant.git
- py -3.11 -m venv .venv
- .venv\Scripts\pip install pandas==2.2.3 numpy==1.26.4
- .venv\Scripts\python -c "from src.data.sample_data import save_all_samples; save_all_samples()"

## Errors / issues
- gh CLI not on PATH after winget install — resolved by refreshing PATH in PowerShell session.
- pandas not found when running sample_data.py before venv was set up — resolved by creating venv and installing dependencies first.

## Decisions made
- Python 3.11 (py launcher, .venv)
- LLM provider: Anthropic, env var: ANTHROPIC_API_KEY
- Synthetic sample data first (GBM, fixed seed 42); real data downloaded later via yfinance
- GitHub repo: private until fully polished
- Runnable core (Phases 1–6 + 8) before deployment polish
- MCP via official mcp Python SDK
- FAISS for RAG vector store (no switching mid-project)
- Requirements pinned from day one

## Next exact task
Phase 2 — Core financial risk engine
Start with src/data/loaders.py and src/data/validators.py, then build all risk modules (returns, volatility, drawdown, var, rolling), then tests.

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.

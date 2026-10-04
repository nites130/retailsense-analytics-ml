# RetailSense
### Sales Analytics & Customer Purchase Prediction — Version 3

Already running version 1? Follow [UPDATE_EXISTING.md](UPDATE_EXISTING.md) to keep your database and environment.

New: complete marketing website, signup/login/logout, hashed passwords, isolated account workspaces, graphite/mint UI, light/dark mode, SVG revenue chart, combined date/country filters, market breakdown, business observations and customer profile drill-down.

A local full-stack retail analytics application combining a responsive web frontend, Flask REST API, SQLite persistence, data cleaning, RFM segments and out-of-time machine-learning evaluation.

**Start with [START_HERE.md](START_HERE.md)** for Windows + VS Code instructions.

## Features

- Responsive overview dashboard: gross purchase revenue, order count, average order value, monthly revenue, products and customer segments.
- Country filtering, customer ID search, segment filters and pagination.
- CSV import with validation and a transparent cleaning report.
- Deterministic synthetic demo (seed 42); no downloaded dataset required to start.
- Logistic Regression vs Random Forest selection on validation F1.
- Later held-out test metrics: precision, recall, F1, ROC AUC, Brier score and a prior baseline.
- 30-day repeat-purchase probabilities for existing customers, as of the dataset end.
- Customer CSV export, local SQLite storage and automatic model-result invalidation on import.

## Stack and architecture

Browser (HTML/CSS/JavaScript) → Flask JSON API → Pandas analytics / scikit-learn → SQLite.

No Node.js, paid APIs, API keys, remote fonts or chart CDNs. Database is created automatically in `data/retailsense-user-<id>.sqlite3`. Model results and scores survive restart; estimator objects are not pickled. Retrain to generate new scores after an import.

## Quick start

Tested on Python 3.12. Windows commands are in START_HERE.md.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Create an account, load demo in your workspace, explore analytics, then train in Prediction lab.

## Repository map

| File | Purpose |
| --- | --- |
| app.py | Flask routes, input handling and SQLite persistence |
| analytics.py | Cleaning, metrics, RFM rules, feature creation, seeded data |
| ml.py | Temporal snapshots, model selection, evaluation and scoring |
| templates/index.html | App interface |
| static/ | Responsive CSS and API-connected JavaScript |
| tests/test_app.py | Integration and data leakage checks |
| docs/SQL_QUERIES.sql | Business analysis queries for SQLite |
| docs/SHOWCASE.md | GitHub, LinkedIn and resume preparation |
| docs/MODEL_CARD.md | ML assumptions and limitations |

## Real dataset

Use [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) (Daqing Chen, 2015; DOI: 10.24432/C5BW33). Its historical transactions cover December 2010–December 2011. Follow the dataset's attribution/license terms (CC BY 4.0 listed by UCI). Download the Excel workbook, open it in Excel and save as **CSV UTF-8 (comma-delimited)**. No real UCI data is bundled or claimed to have been evaluated here.

Required columns:
`InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country`

Use unambiguous ISO dates where possible; UCI US-style dates are parsed month-first. Avoid ambiguous day-first date exports. Use one currency (display is GBP). Maximum upload 50 MB.

Cancellation invoices, non-positive quantities/prices, invalid dates/numbers and missing IDs are excluded. Exact duplicates are removed; this assumption can remove legitimate identical lines and should be checked on your source. Missing product descriptions become “Unnamed product.” Anonymous purchases are excluded from both sales and customer metrics. Revenue is **gross valid purchases for identified customers**, not net revenue, profit, or total reported company revenue.

## API

GET: `/api/status`, `/api/dashboard?country=Germany`, `/api/customers?q=100&page=1&segment=Loyal`, `/api/export`, `/api/template`.

POST: `/api/demo`, `/api/import` (multipart field `file`), `/api/train`. POST requests require header `X-RetailSense: local-app`; browser code sends it automatically. No CORS is enabled.

## Validation

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover empty state, demo/import, metric totals, filtering, training and probability bounds, reset invalidation, rejected-file preservation, persistence and feature leakage. Browser visual testing was unavailable in the build environment; verify desktop/mobile layout locally before recording a showcase.

## Scope

Local portfolio website bound to 127.0.0.1, with signup/login, hashed passwords, signed HTTP-only SameSite sessions, basic in-memory login throttling and per-account SQLite databases. Do not expose the development server to the internet. Public deployment still needs HTTPS with Secure cookies, production WSGI hosting, persistent rate limiting, recovery/email verification, background ML jobs and an upload policy. Do not commit personal customer data or database files. Files are ignored by .gitignore.

Dependencies use compatible ranges for installation flexibility. `docs/TESTED_VERSIONS.txt` records the build's tested versions.

## Account storage

Accounts are stored in `data/retailsense-accounts.sqlite3`. Each account has its own `retailsense-user-<id>.sqlite3`. Session signing key is stored in `data/.session-secret`; never publish the data folder. Imported data remains separate across accounts. Email is a local login identifier; no email is sent. Password recovery is not implemented.

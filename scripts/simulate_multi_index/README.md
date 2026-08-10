# Multi-Index Elasticsearch Mutation Simulator & Verification Suite

This toolset automates post-upgrade data mutation simulations (Create / Update / Delete) across multiple Elasticsearch indices and audits the reconciliation integrity between clusters.

It is available in both **Pure Shell (Bash)** and **Python** implementations:

- **`sh/`**: Pure Bash scripts (100% `bash`, `curl`, `jq`) designed for CI/CD runners without Python dependencies.
- **`python/`**: Python core scripts (`urllib`, `json`) for rich local development and debugging.

---

## ⚙️ Environment Variables & Default Ratios

All scripts prioritize environment variables over hardcoded defaults:

| Environment Variable | Description | Default Value |
| :--- | :--- | :--- |
| `ES_URL` | Base URL of target Elasticsearch cluster | `http://localhost:9200` (fallbacks: `ES9_URL`, `ES6_URL`) |
| `ES_USER` | Basic auth username | `elastic` |
| `ES_PASS` / `ES_PW` | Basic auth password | `""` |
| `INDICES` | Comma-separated list of target indices | Discovered automatically from templates |
| `SAMPLE_FILE` | Path to **JSON file** or **Directory** containing templates | `sample_templates.json` |
| `REPORT_FILE` | Path to save simulation report JSON | `report.json` |
| `MUTATE_PCT` | Fraction of total index count to mutate | `0.10` (10%) |
| `CREATE_RATIO` | Share of total mutations allocated to Creates | **`0.30` (30%)** |
| `UPDATE_RATIO` | Share of total mutations allocated to Updates | **`0.60` (60%)** |
| `DELETE_RATIO` | Share of total mutations allocated to Deletes | **`0.10` (10%)** |
| `TOTAL_MUTATIONS` | Fixed number of mutations per index (overrides `MUTATE_PCT`) | `""` (Calculated automatically) |
| `SUFFIX` | Suffix for index cloning tool | `_upgrade` |

---

## 🚀 Quick Start Guide

### Pure Shell Suite
```bash
# Run Pure Shell Simulation (30% Create / 60% Update / 10% Delete)
bash scripts/simulate_multi_index/sh/simulate_multi_index.sh

# Run Pure Shell Verification Audit
bash scripts/simulate_multi_index/sh/verify_multi_index.sh
```

### Python Suite
```bash
# Run Python Simulation
python scripts/simulate_multi_index/python/simulate_multi_index.py

# Run Python Verification Audit
python scripts/simulate_multi_index/python/verify_multi_index.py
```

# Fin Metrics Pipeline

One‑shot ETL + loader that pulls the last five fiscal‑year metrics from Financial Modeling Prep
and inserts them into the Postgres schema used by our dashboard.

## Folder structure

```
fin-metrics-pipeline/
├── README.md
├── requirements.txt
├── sql/
│   ├── 01_schema.sql
│   └── 02_seed_reference_data.sql
├── etl/
│   └── etl_rpd_last5.py
└── loader/
    └── load_to_pg.py
```

## Quick start

```bash
git clone https://github.com/sidobagga/finmetrics.git
cd fin-metrics-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1 — create tables & reference rows
psql $PG_URL -f sql/01_schema.sql
psql $PG_URL -f sql/02_seed_reference_data.sql

# 2 — fetch + melt to CSV
python etl/etl_rpd_last5.py           # writes ~/Downloads/RPD_last5_metrics_<date>.csv

# 3 — upsert into Postgres
python loader/load_to_pg.py           # reads CSV and upserts into financial_metrics
```

Set env‑vars:

* `PG_URL` – full SQLAlchemy/Postgres URL, e.g. `postgresql://user:pass@host/db`
* `FMP_KEY` – your Financial Modeling Prep API key

## Smoke test

After running `load_to_pg.py`:

```sql
SELECT fy, metric_code, value_numeric
FROM   financial_metrics m
JOIN   periods p USING (period_id)    -- if you add the periods dim
WHERE  company_id = 'RPD'
ORDER  BY fy DESC, metric_code
LIMIT 20;
```

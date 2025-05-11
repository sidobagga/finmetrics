"""Load the tall CSV from ~/Downloads into Postgres financial_metrics table."""
import os, pandas as pd, psycopg2, psycopg2.extras as ext
from pathlib import Path
from datetime import datetime

PG_URL = os.getenv('PG_URL')
if not PG_URL:
    raise SystemExit('Set PG_URL env‑var pointing at your Postgres database')

TICKER = 'RPD'
# pick latest CSV in Downloads
downloads = Path.home() / 'Downloads'
candidates = sorted(downloads.glob(f'{TICKER}_last5_metrics_*.csv'))
if not candidates:
    raise SystemExit('No CSV found in Downloads/ – run the ETL script first')
csv_path = candidates[-1]

df = pd.read_csv(csv_path)
conn = psycopg2.connect(PG_URL)
cur  = conn.cursor()

cur.execute("SELECT company_id FROM companies WHERE ticker=%s", (TICKER,))
company_id = cur.fetchone()[0]

cur.execute("SELECT source_id FROM data_sources WHERE source_name=%s", ('Financial Modeling Prep',))
source_id = cur.fetchone()[0]

rows = []
for r in df.itertuples(index=False):
    # period_id is FY for now
    val_num = float(r.value) if not pd.isna(r.value) else None
    rows.append((r.FY, source_id, company_id, r.metric, val_num, None, None))

ext.execute_values(cur, """
    INSERT INTO financial_metrics
      (period_id, source_id, company_id, metric_code,
       value_numeric, value_int, unit)
    VALUES %s
    ON CONFLICT (period_id, source_id, company_id, metric_code)
    DO UPDATE SET value_numeric = EXCLUDED.value_numeric,
                  collected_at  = now();
""", rows, page_size=500)

conn.commit(); conn.close()
print(f'Loaded {len(rows)} rows from {csv_path} into financial_metrics')

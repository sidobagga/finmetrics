"""Fetch last‑5 FY metrics for RPD from Financial Modeling Prep and
save a tall CSV into ~/Downloads/."""
import os, requests, pandas as pd
from pathlib import Path
from datetime import datetime

API_KEY = 'JHqiU8ZuKCkuC5GxLWGJMJ02SBKhAyIv'

API_BASE = "https://financialmodelingprep.com/api/v3"
TICKER   = "RPD"
CURRENT  = datetime.utcnow().year
YEARS    = list(range(CURRENT - 1, CURRENT - 6, -1))

ENDPOINTS = {
    "income"     : ("income-statement",        True),
    "balance"    : ("balance-sheet-statement", False),
    "cashflow"   : ("cash-flow-statement",     False),
    "enterprise" : ("enterprise-values",       False),
    "metrics"    : ("key-metrics",             False),
}

MAP = {
    "sales": "revenue",
    "ebit": "operatingIncome",
    "ebitda": "ebitda",
    "net_income": "netIncome",
    "ocf": "operatingCashFlow",
    "capex": "capitalExpenditure",
    "free_cf": "freeCashFlow",
    "basic_shares": "sharesOutstanding",
    "fd_shares": "weightedAverageDilutedSharesOutstanding",
    "market_cap": "marketCap",
    "enterprise_value": "enterpriseValue",
    "total_debt": "totalDebt",
    "cash_equivalents": "cashAndShortTermInvestments",
    "ev_ebitda": "enterpriseValueOverEBITDA",
    "ev_sales": "evToSales",
    "price_earnings": "peRatio",
}

def fetch(path, use_cal_yr):
    url = f"{API_BASE}/{path}/{TICKER}?apikey={API_KEY}&limit=120"
    df = pd.DataFrame(requests.get(url, timeout=30).json())
    if df.empty:
        return df
    if use_cal_yr and 'calendarYear' in df.columns:
        df['FY'] = df['calendarYear']
    else:
        df['FY'] = pd.to_datetime(df['date']).dt.year
    return df[df['FY'].isin(YEARS)].reset_index(drop=True)

dfs, recs = {}, []
for sec,(path,use_y) in ENDPOINTS.items():
    df = fetch(path,use_y)
    if df.empty:
        continue
    dfs[sec] = df

# derived
ent = dfs.get('enterprise', pd.DataFrame())
if not ent.empty:
    ent['fd_market_cap'] = (
        ent['marketCap'] * ent['weightedAverageDilutedSharesOutstanding'] / ent['sharesOutstanding']
    )

bal = dfs.get('balance', pd.DataFrame())
if not bal.empty and {'totalDebt','cashAndShortTermInvestments'} <= set(bal.columns):
    bal['net_debt'] = bal['totalDebt'] - bal['cashAndShortTermInvestments']

# build tall
for sec, df in dfs.items():
    avail = {k:v for k,v in MAP.items() if v in df.columns}
    subset = df[['FY', *avail.values()]].rename(columns={v:k for k,v in avail.items()})
    tall = subset.melt(id_vars='FY', var_name='metric', value_name='value').dropna(subset=['value'])
    recs.append(tall)

tall_df = pd.concat(recs, ignore_index=True).sort_values(['metric','FY'], ascending=[True,False])

out_path = Path.home()/'Downloads'/f'{TICKER}_last5_metrics_{datetime.utcnow():%Y%m%d}.csv'
tall_df.to_csv(out_path, index=False)
print(f'Wrote {len(tall_df)} rows → {out_path}')

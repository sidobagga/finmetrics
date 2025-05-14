"""Fetch last‑5 FY metrics for a company from Financial Modeling Prep and
save a tall CSV into ~/Downloads/."""
import os, requests, pandas as pd
import argparse
from pathlib import Path
from datetime import datetime

API_KEY = 'fjRDKKnsRnVNMfFepDM6ox31u9RlPklv'
API_BASE = "https://financialmodelingprep.com/api/v3"
CURRENT  = datetime.utcnow().year
YEARS    = list(range(CURRENT - 1, CURRENT - 6, -1))

ENDPOINTS = {
    "income"     : ("income-statement",        True),
    "balance"    : ("balance-sheet-statement", False),
    "cashflow"   : ("cash-flow-statement",     False),
    "enterprise" : ("enterprise-values",       False),
    "metrics"    : ("key-metrics",             False),
}

# Updated mapping to match actual API response column names
MAP = {
    "sales": "revenue",
    "ebit": "operatingIncome",
    "ebitda": "ebitda",
    "net_income": "netIncome",
    "ocf": "operatingCashFlow",
    "capex": "capitalExpenditure",
    "free_cf": "freeCashFlow",
    "basic_shares": "numberOfShares",  # Updated from sharesOutstanding
    "fd_shares": "weightedAverageShsOutDil",  # Updated from weightedAverageDilutedSharesOutstanding
    "market_cap": "marketCapitalization",  # Updated from marketCap
    "enterprise_value": "enterpriseValue",
    "total_debt": "totalDebt",
    "cash_equivalents": "cashAndShortTermInvestments",
    "ev_ebitda": "enterpriseValueOverEBITDA",
    "ev_sales": "evToSales",
    "price_earnings": "peRatio",
}

def fetch(ticker, path, use_cal_yr):
    url = f"{API_BASE}/{path}/{ticker}?apikey={API_KEY}&limit=120"
    try:
        response = requests.get(url, timeout=30).json()
        
        df = pd.DataFrame(response)
        if df.empty:
            print(f"No data found for {ticker} in {path}")
            return df
        
        if use_cal_yr and 'calendarYear' in df.columns:
            df['FY'] = df['calendarYear']
        else:
            df['FY'] = pd.to_datetime(df['date']).dt.year
        return df[df['FY'].isin(YEARS)].reset_index(drop=True)
    except Exception as e:
        print(f"Error fetching {path} for {ticker}: {e}")
        return pd.DataFrame()

def process_ticker(ticker):
    ticker = ticker.upper()
    print(f"Processing data for {ticker}...")
    
    dfs, recs = {}, []
    for sec,(path,use_y) in ENDPOINTS.items():
        df = fetch(ticker, path, use_y)
        if df.empty:
            continue
        dfs[sec] = df

    # derived
    ent = dfs.get('enterprise', pd.DataFrame())
    if not ent.empty:
        # Check for fd_market_cap required columns
        if 'marketCapitalization' in ent.columns:
            # For fd_market_cap calculation we need the diluted shares
            # First check if we can get it from the income statement
            income_df = dfs.get('income', pd.DataFrame())
            if not income_df.empty and 'weightedAverageShsOutDil' in income_df.columns:
                # Join the required column from income statement
                latest_income = income_df.sort_values('FY', ascending=False).iloc[0]
                ent['weightedAverageShsOutDil'] = latest_income['weightedAverageShsOutDil']
                
                if 'numberOfShares' in ent.columns and 'weightedAverageShsOutDil' in ent.columns:
                    ent['fd_market_cap'] = (
                        ent['marketCapitalization'] * ent['weightedAverageShsOutDil'] / ent['numberOfShares']
                    )

    bal = dfs.get('balance', pd.DataFrame())
    if not bal.empty and {'totalDebt','cashAndShortTermInvestments'} <= set(bal.columns):
        bal['net_debt'] = bal['totalDebt'] - bal['cashAndShortTermInvestments']

    # build tall
    for sec, df in dfs.items():
        # Find available metrics in this dataframe
        avail = {}
        for k, v in MAP.items():
            if v in df.columns:
                avail[k] = v
        
        if not avail:
            continue
            
        # Ensure FY column exists
        if 'FY' not in df.columns:
            continue
        
        # Select only available columns
        columns_to_use = ['FY'] + list(avail.values())
        subset = df[columns_to_use].rename(columns={v:k for k,v in avail.items()})
        tall = subset.melt(id_vars='FY', var_name='metric', value_name='value').dropna(subset=['value'])
        recs.append(tall)

    # Only proceed if we have data
    if recs:
        tall_df = pd.concat(recs, ignore_index=True).sort_values(['metric','FY'], ascending=[True,False])
        
        out_path = Path.home()/'Downloads'/f'{ticker}_last5_metrics_{datetime.utcnow():%Y%m%d}.csv'
        tall_df.to_csv(out_path, index=False)
        print(f'Wrote {len(tall_df)} rows → {out_path}')
        return out_path
    else:
        print(f"No data was collected for {ticker}. Please check API access and ticker symbol.")
        return None

def main():
    parser = argparse.ArgumentParser(description='Fetch last 5 years of financial metrics for a company')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., RPD, AAPL)')
    args = parser.parse_args()
    
    process_ticker(args.ticker)

if __name__ == "__main__":
    main()

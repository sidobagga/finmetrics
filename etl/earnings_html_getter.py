import json, re, time, requests
HEADERS = {
    "User-Agent": "MyFinDataCrawler/1.0 (sid@example.com)",
    "Accept-Encoding": "gzip, deflate",
}

CIK_MAP_URL = "https://www.sec.gov/files/company_tickers_exchange.json"

def load_ticker_map(cache_path="cik_map.json"):
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        data = requests.get(CIK_MAP_URL, headers=HEADERS, timeout=30).json()
        with open(cache_path, "w") as f:
            json.dump(data, f)
        return data

def cik_from_ticker(ticker, cik_map):
    # The cik_map structure is a dict with 'data' key containing a list of entries
    # Each entry is a list with [cik, name, ticker, exchange]
    ticker_upper = ticker.upper()
    for entry in cik_map['data']:
        if entry[2] == ticker_upper:  # Index 2 contains the ticker symbol
            return f'{entry[0]:010d}'  # Index 0 contains the CIK
    raise ValueError(f"Ticker {ticker} not found in CIK map")

def recent_8k_accessions(cik, max_rows=40):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    sub = requests.get(url, headers=HEADERS, timeout=30).json()
    recent = sub["filings"]["recent"]
    return [
        (a, d) for a, d, f in zip(recent["accessionNumber"],
                                  recent["filingDate"],
                                  recent["form"])
        if f.startswith("8-K")
    ][:max_rows]

EX99_RE = re.compile(r"ex.*99.*\.htm$", re.I)
KEY_RE  = re.compile(r"(earn|press).*\.htm$", re.I)

def earnings_release_url(cik, accession):
    acc_nodash = accession.replace("-", "")
    idx_url = (f"https://www.sec.gov/Archives/edgar/data/"
               f"{int(cik)}/{acc_nodash}/index.json")
    idx = requests.get(idx_url, headers=HEADERS, timeout=30).json()
    files = [item["name"] for item in idx["directory"]["item"]]

    for regex in (EX99_RE, KEY_RE):
        for fname in files:
            if regex.search(fname):
                return idx_url.replace("index.json", fname)
    return None

def get_latest_release(ticker):
    cik_map = load_ticker_map()
    cik = cik_from_ticker(ticker, cik_map)
    for accession, date in recent_8k_accessions(cik):
        url = earnings_release_url(cik, accession)
        if url:
            return {"ticker": ticker.upper(),
                    "filing_date": date,
                    "release_url": url}
        time.sleep(0.12)      # ~8 req/s overall
    return None

# Example
if __name__ == "__main__":
    print(get_latest_release("IBM")) 
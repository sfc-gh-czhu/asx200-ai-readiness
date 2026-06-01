#!/usr/bin/env python3
"""Fetch S&P/ASX 200 constituents from Wikipedia and write COMPANY CSV."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

WIKI_URL = "https://en.wikipedia.org/wiki/S%26P/ASX_200"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "company.csv"


def company_id(ticker: str) -> str:
    return hashlib.sha256(ticker.upper().encode()).hexdigest()[:16]


def normalize_ticker(raw: str) -> str:
    t = raw.strip().upper()
    if not t.endswith(".AX"):
        t = f"{t}.AX"
    return t


def fetch_asx200() -> pd.DataFrame:
    headers = {"User-Agent": "asx200-ai-readiness/0.1 (research; +https://github.com/Snowflake-Labs/cortex-code-skills)"}
    resp = requests.get(WIKI_URL, headers=headers, timeout=60)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    tables = soup.select("table.wikitable")
    if not tables:
        raise RuntimeError("No wikitable found on Wikipedia ASX 200 page")

    rows: list[dict] = []
    for table in tables:
        headers_row = [th.get_text(strip=True) for th in table.select("tr th")]
        if not headers_row:
            continue
        header_lower = " ".join(headers_row).lower()
        if "code" not in header_lower and "ticker" not in header_lower:
            continue
        for tr in table.select("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            if len(cells) < 2:
                continue
            ticker_raw = cells[0]
            name = cells[1] if len(cells) > 1 else ""
            sector = cells[2] if len(cells) > 2 else None
            if not ticker_raw or not name:
                continue
            ticker = normalize_ticker(re.sub(r"[^A-Za-z0-9.]", "", ticker_raw.split()[0]))
            rows.append(
                {
                    "COMPANY_ID": company_id(ticker),
                    "ASX_TICKER": ticker,
                    "COMPANY_NAME": name,
                    "GICS_SECTOR": sector,
                    "GICS_INDUSTRY": None,
                    "MARKET_CAP_AUD": None,
                    "HQ_CITY": None,
                    "HQ_COUNTRY": "AU",
                    "EMPLOYEE_COUNT": None,
                    "WEBSITE_URL": None,
                    "CAREERS_URL": None,
                    "IR_URL": None,
                    "BLOG_URL": None,
                    "GOVERNANCE_URL": None,
                }
            )
        if rows:
            break

    if not rows:
        raise RuntimeError("Could not parse ASX 200 table from Wikipedia")

    df = pd.DataFrame(rows).drop_duplicates(subset=["ASX_TICKER"])
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    df = fetch_asx200()
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} companies to {args.output}")


if __name__ == "__main__":
    main()

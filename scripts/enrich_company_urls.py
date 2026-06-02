#!/usr/bin/env python3
"""Resolve company website and dimension URLs; update CSV and optionally Snowflake COMPANY."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_tickers import PILOT_TICKERS  # noqa: E402

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "company.csv"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "enriched_urls.csv"
UA = "asx200-ai-readiness/0.1 (+https://github.com/sfc-gh-czhu/asx200-ai-readiness)"

# Known domains for pilot (reduces failed guesses)
PILOT_DOMAINS: dict[str, str] = {
    "CBA.AX": "https://www.commbank.com.au",
    "BHP.AX": "https://www.bhp.com",
    "CSL.AX": "https://www.csl.com",
    "XRO.AX": "https://www.xero.com",
    "TLS.AX": "https://www.telstra.com.au",
    "WOW.AX": "https://www.woolworthsgroup.com.au",
    "MQG.AX": "https://www.macquarie.com",
    "WTC.AX": "https://www.wisetechglobal.com",
    "QAN.AX": "https://www.qantas.com",
    "COH.AX": "https://www.cochlear.com",
}

DIMENSION_PATHS = {
    "careers": ["/careers", "/jobs", "/work-with-us", "/join-us"],
    "ir": ["/investors", "/investor-relations", "/investor-centre", "/about/investors"],
    "blog": ["/blog", "/engineering", "/tech", "/insights/blog", "/news/technology"],
    "governance": [
        "/governance",
        "/about/governance",
        "/corporate-governance",
        "/responsibility/ai",
        "/about/policies",
        "/privacy",
    ],
}


def slug_from_name(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "", name.lower())
    return s[:30] if s else "company"


def guess_website(ticker: str, name: str) -> str | None:
    if ticker in PILOT_DOMAINS:
        return PILOT_DOMAINS[ticker]
    base = slug_from_name(name.split()[0] if name else ticker.replace(".AX", ""))
    for domain in [f"https://www.{base}.com.au", f"https://www.{base}.com", f"https://{base}.com.au"]:
        try:
            r = requests.head(domain, headers={"User-Agent": UA}, timeout=8, allow_redirects=True)
            if r.status_code < 400:
                return r.url if hasattr(r, "url") else domain
        except requests.RequestException:
            continue
    return None


def find_link_on_page(base_url: str, path_candidates: list[str]) -> str | None:
    for path in path_candidates:
        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=15, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 500:
                return r.url
        except requests.RequestException:
            continue
    try:
        r = requests.get(base_url, headers={"User-Agent": UA}, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "lxml")
        keywords = path_candidates[0].strip("/").split("/")[0].lower()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").lower()
            if keywords in href.lower() or keywords in text:
                return urljoin(base_url, href)
    except requests.RequestException:
        pass
    return None


def annual_report_url(ir_url: str | None, website: str | None) -> str | None:
    base = ir_url or website
    if not base:
        return None
    for path in ["/annual-reports", "/reports", "/financial-reports", "/investors/reports"]:
        url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                return r.url
        except requests.RequestException:
            continue
    return base


def enrich_row_fast(row: pd.Series, website: str | None) -> pd.Series:
    row = row.copy()
    if not website:
        return row
    base = website.rstrip("/")
    row["WEBSITE_URL"] = website
    row["CAREERS_URL"] = f"{base}/careers"
    row["IR_URL"] = f"{base}/investors"
    row["BLOG_URL"] = f"{base}/blog"
    row["GOVERNANCE_URL"] = f"{base}/governance"
    row["ANNUAL_REPORT_URL"] = f"{base}/investors"
    return row


def enrich_row(row: pd.Series, delay: float) -> pd.Series:
    ticker = row["ASX_TICKER"]
    website = row.get("WEBSITE_URL") if pd.notna(row.get("WEBSITE_URL")) else None
    if not website:
        website = guess_website(ticker, row["COMPANY_NAME"])
        time.sleep(delay)

    careers = row.get("CAREERS_URL") if pd.notna(row.get("CAREERS_URL")) else None
    ir = row.get("IR_URL") if pd.notna(row.get("IR_URL")) else None
    blog = row.get("BLOG_URL") if pd.notna(row.get("BLOG_URL")) else None
    gov = row.get("GOVERNANCE_URL") if pd.notna(row.get("GOVERNANCE_URL")) else None

    if website:
        if not careers:
            careers = find_link_on_page(website, DIMENSION_PATHS["careers"])
            time.sleep(delay)
        if not ir:
            ir = find_link_on_page(website, DIMENSION_PATHS["ir"])
            time.sleep(delay)
        if not blog:
            blog = find_link_on_page(website, DIMENSION_PATHS["blog"])
            time.sleep(delay)
        if not gov:
            gov = find_link_on_page(website, DIMENSION_PATHS["governance"])
            time.sleep(delay)

    row = row.copy()
    row["WEBSITE_URL"] = website
    row["CAREERS_URL"] = careers
    row["IR_URL"] = ir
    row["BLOG_URL"] = blog
    row["GOVERNANCE_URL"] = gov
    row["ANNUAL_REPORT_URL"] = annual_report_url(ir, website)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pilot", action="store_true", help="Only pilot tickers")
    parser.add_argument("--all", action="store_true", help="All companies in CSV")
    parser.add_argument("--exclude-pilot", action="store_true", help="Skip pilot tickers (for scale run)")
    parser.add_argument("--fast", action="store_true", help="Template URLs only, no per-path HTTP probes")
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if args.pilot:
        df = df[df["ASX_TICKER"].isin(PILOT_TICKERS)]
    if args.exclude_pilot:
        df = df[~df["ASX_TICKER"].isin(PILOT_TICKERS)]
    if args.limit:
        df = df.head(args.limit)

    enriched = []
    for i, (_, row) in enumerate(df.iterrows()):
        print(f"[{i+1}/{len(df)}] {row['ASX_TICKER']} {row['COMPANY_NAME']}")
        if args.fast:
            website = row.get("WEBSITE_URL") if pd.notna(row.get("WEBSITE_URL")) else None
            if not website:
                website = guess_website(row["ASX_TICKER"], row["COMPANY_NAME"])
            enriched.append(enrich_row_fast(row, website))
        else:
            enriched.append(enrich_row(row, args.delay))

    out = pd.DataFrame(enriched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Wrote {len(out)} rows to {args.output}")


if __name__ == "__main__":
    main()

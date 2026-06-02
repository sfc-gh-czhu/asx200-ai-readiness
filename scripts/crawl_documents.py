#!/usr/bin/env python3
"""Crawl dimension URLs and write RAW_DOCUMENT records to JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_tickers import PILOT_TICKERS  # noqa: E402

DEFAULT_ENRICHED = Path(__file__).resolve().parent.parent / "data" / "enriched_urls.csv"
DEFAULT_COMPANY = Path(__file__).resolve().parent.parent / "data" / "company.csv"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "raw_documents.jsonl"
UA = "asx200-ai-readiness/0.1 (+https://github.com/sfc-gh-czhu/asx200-ai-readiness)"
MAX_TEXT = 500_000


def doc_id(company_id: str, dimension: str, url: str) -> str:
    raw = f"{company_id}|{dimension}|{url}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:MAX_TEXT]


def extract_pdf_bytes(data: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        parts = []
        for page in reader.pages[:50]:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)[:MAX_TEXT]
    except Exception as e:
        return f"[PDF parse error: {e}]"


def fetch_url(url: str, timeout: int = 30) -> tuple[str, str, str]:
    """Returns (status, content_type, raw_text)."""
    if not url or not str(url).startswith("http"):
        return "not_found", "", ""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.status_code == 403:
            return "blocked", r.headers.get("Content-Type", ""), ""
        if r.status_code == 404:
            return "not_found", "", ""
        if r.status_code >= 400:
            return "error", "", f"HTTP {r.status_code}"

        ctype = (r.headers.get("Content-Type") or "").lower()
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            text = extract_pdf_bytes(r.content)
            return ("ok" if len(text) > 200 else "error"), "application/pdf", text

        if "html" in ctype or "text" in ctype or not ctype:
            text = extract_html_text(r.text)
            return ("ok" if len(text) > 200 else "error"), "text/html", text

        return "error", ctype, ""
    except requests.Timeout:
        return "error", "", "timeout"
    except requests.RequestException as e:
        return "error", "", str(e)[:500]


def dimension_urls(row: pd.Series) -> list[tuple[str, str]]:
    """dimension, url"""
    urls = []
    if pd.notna(row.get("GOVERNANCE_URL")) and row.get("GOVERNANCE_URL"):
        urls.append(("governance", str(row["GOVERNANCE_URL"])))
    ar = row.get("ANNUAL_REPORT_URL") or row.get("IR_URL")
    if pd.notna(ar) and ar:
        urls.append(("annual_report", str(ar)))
    if pd.notna(row.get("CAREERS_URL")) and row.get("CAREERS_URL"):
        urls.append(("hiring", str(row["CAREERS_URL"])))
    if pd.notna(row.get("BLOG_URL")) and row.get("BLOG_URL"):
        urls.append(("engineering_blog", str(row["BLOG_URL"])))
    if pd.notna(row.get("WEBSITE_URL")) and row.get("WEBSITE_URL"):
        base = str(row["WEBSITE_URL"])
        urls.append(("procurement", urljoin_procurement(base)))
    return urls


def urljoin_procurement(base: str) -> str:
    from urllib.parse import urljoin

    for path in ["/procurement", "/suppliers", "/about/policies", "/governance/policies"]:
        return urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    return base


def crawl_dataframe(df: pd.DataFrame, delay: float) -> list[dict]:
    records: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()
    for _, row in df.iterrows():
        cid = row["COMPANY_ID"]
        for dimension, url in dimension_urls(row):
            status, ctype, text = fetch_url(url)
            time.sleep(delay)
            rec = {
                "DOC_ID": doc_id(cid, dimension, url),
                "COMPANY_ID": cid,
                "ASX_TICKER": row["ASX_TICKER"],
                "DIMENSION": dimension,
                "SOURCE_URL": url,
                "RAW_TEXT": text,
                "CONTENT_TYPE": ctype,
                "FETCH_STATUS": status,
                "FETCHED_AT": now,
            }
            records.append(rec)
            print(f"  {row['ASX_TICKER']} {dimension}: {status} ({len(text)} chars)")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=None, help="enriched_urls.csv")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--all", action="store_true", help="Crawl all rows in input")
    parser.add_argument("--exclude-pilot", action="store_true", help="Skip pilot tickers")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    inp = args.input or (DEFAULT_ENRICHED if DEFAULT_ENRICHED.exists() else DEFAULT_COMPANY)
    if not inp.exists():
        raise SystemExit(f"Missing input {inp}. Run enrich_company_urls.py first.")

    df = pd.read_csv(inp)
    if args.pilot:
        df = df[df["ASX_TICKER"].isin(PILOT_TICKERS)]
    if args.exclude_pilot:
        df = df[~df["ASX_TICKER"].isin(PILOT_TICKERS)]

    print(f"Crawling {len(df)} companies from {inp}")
    records = crawl_dataframe(df, args.delay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    with open(args.output, mode, encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    ok = sum(1 for r in records if r["FETCH_STATUS"] == "ok")
    print(f"Wrote {len(records)} documents to {args.output} ({ok} ok)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Load COMPANY CSV into AI_READINESS_DB.ASX200.COMPANY via Snowflake connector."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

try:
    import snowflake.connector
except ImportError as e:
    raise SystemExit("Install deps: uv sync") from e

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "company.csv"
TABLE = "AI_READINESS_DB.ASX200.COMPANY"

COLUMNS = [
    "COMPANY_ID",
    "ASX_TICKER",
    "COMPANY_NAME",
    "GICS_SECTOR",
    "GICS_INDUSTRY",
    "MARKET_CAP_AUD",
    "HQ_CITY",
    "HQ_COUNTRY",
    "EMPLOYEE_COUNT",
    "WEBSITE_URL",
    "CAREERS_URL",
    "IR_URL",
    "BLOG_URL",
    "GOVERNANCE_URL",
]


def connect(connection_name: str | None):
    """Connect using env vars or Snowflake externalbrowser (connections.toml name)."""
    conn_name = connection_name or os.environ.get("SNOWFLAKE_CONNECTION", "sfseapac-au_demo70")
    # snowflake-connector reads ~/.snowflake/connections.toml when using connection_name
    return snowflake.connector.connect(
        connection_name=conn_name,
        authenticator=os.environ.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        database="AI_READINESS_DB",
        schema="ASX200",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--connection", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--truncate", action="store_true", help="DELETE FROM COMPANY before load")
    args = parser.parse_args()

    if not args.csv.exists():
        raise SystemExit(f"Missing {args.csv}. Run: uv run python scripts/get_asx200_list.py")

    df = pd.read_csv(args.csv)
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise SystemExit(f"CSV missing columns: {missing}")

    print(f"Loaded {len(df)} rows from {args.csv}")
    if args.dry_run:
        print(df[["ASX_TICKER", "COMPANY_NAME", "GICS_SECTOR"]].head(10).to_string())
        return

    conn = connect(args.connection)
    try:
        cur = conn.cursor()
        if args.truncate:
            cur.execute(f"DELETE FROM {TABLE}")
        placeholders = ", ".join(["%s"] * len(COLUMNS))
        sql = (
            f"INSERT INTO {TABLE} ({', '.join(COLUMNS)}) "
            f"VALUES ({placeholders})"
        )
        rows = [tuple(row[c] if pd.notna(row[c]) else None for c in COLUMNS) for _, row in df.iterrows()]
        cur.executemany(sql, rows)
        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
        count = cur.fetchone()[0]
        print(f"Inserted into {TABLE}. Total rows: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

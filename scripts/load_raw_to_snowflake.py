#!/usr/bin/env python3
"""Load RAW_DOCUMENT rows from JSONL into Snowflake."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from snowflake_util import connect

TABLE = "AI_READINESS_DB.ASX200.RAW_DOCUMENT"
COLS = [
    "DOC_ID",
    "COMPANY_ID",
    "DIMENSION",
    "SOURCE_URL",
    "RAW_TEXT",
    "CONTENT_TYPE",
    "FETCH_STATUS",
    "FETCHED_AT",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", type=Path, required=True)
    parser.add_argument("--connection", default=None)
    parser.add_argument("--truncate", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = []
    with open(args.jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append(
                (
                    obj["DOC_ID"],
                    obj["COMPANY_ID"],
                    obj["DIMENSION"],
                    obj.get("SOURCE_URL"),
                    obj.get("RAW_TEXT") or None,
                    obj.get("CONTENT_TYPE"),
                    obj.get("FETCH_STATUS", "pending"),
                    obj.get("FETCHED_AT"),
                )
            )

    print(f"Loaded {len(rows)} records from {args.jsonl}")
    if args.dry_run:
        from collections import Counter

        print(Counter(r[6] for r in rows))
        return

    conn = connect(args.connection)
    try:
        cur = conn.cursor()
        if args.truncate:
            cur.execute(f"DELETE FROM {TABLE}")
        placeholders = ", ".join(["%s"] * len(COLS))
        merge_sql = f"""
        MERGE INTO {TABLE} t
        USING (SELECT %s AS DOC_ID, %s AS COMPANY_ID, %s AS DIMENSION, %s AS SOURCE_URL,
                      %s AS RAW_TEXT, %s AS CONTENT_TYPE, %s AS FETCH_STATUS, %s AS FETCHED_AT) s
        ON t.DOC_ID = s.DOC_ID
        WHEN MATCHED THEN UPDATE SET
          RAW_TEXT = s.RAW_TEXT, CONTENT_TYPE = s.CONTENT_TYPE,
          FETCH_STATUS = s.FETCH_STATUS, FETCHED_AT = s.FETCHED_AT
        WHEN NOT MATCHED THEN INSERT ({', '.join(COLS)})
          VALUES (s.DOC_ID, s.COMPANY_ID, s.DIMENSION, s.SOURCE_URL, s.RAW_TEXT,
                  s.CONTENT_TYPE, s.FETCH_STATUS, s.FETCHED_AT)
        """
        for row in rows:
            cur.execute(merge_sql, row)
        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
        print(f"{TABLE} total rows: {cur.fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

"""Shared Snowflake connection helpers."""

from __future__ import annotations

import os

import snowflake.connector


def connect(connection_name: str | None = None):
    conn_name = connection_name or os.environ.get("SNOWFLAKE_CONNECTION", "sfseapac-au_demo70")
    return snowflake.connector.connect(
        connection_name=conn_name,
        authenticator=os.environ.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        database="AI_READINESS_DB",
        schema="ASX200",
    )

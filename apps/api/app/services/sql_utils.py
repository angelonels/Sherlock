from __future__ import annotations

from app.services.ingestion_service import quote_ident


def dataset_table_sql(table_name: str) -> str:
    return f"user_data.{quote_ident(table_name)}"

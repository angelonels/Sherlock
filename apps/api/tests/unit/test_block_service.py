import pytest
from pydantic import ValidationError

from app.services.block_service import BlockService


def test_block_service_validates_markdown_kpi_and_table_blocks() -> None:
    service = BlockService()

    blocks = service.validate_blocks(
        [
            {"type": "markdown", "content": "Summary"},
            {"type": "kpi", "label": "Rows", "value": 42},
            {"type": "table", "columns": ["name"], "rows": [{"name": "Aman"}]},
        ]
    )

    assert [block["type"] for block in blocks] == ["markdown", "kpi", "table"]


def test_block_service_rejects_invalid_block_type() -> None:
    with pytest.raises(ValidationError):
        BlockService().validate_block({"type": "tool_trace", "payload": []})


def test_production_filter_removes_debug_blocks() -> None:
    blocks = [{"type": "markdown", "content": "ok"}, {"type": "sql", "content": "SELECT 1"}]

    assert BlockService().filter_for_environment(blocks, "production") == [{"type": "markdown", "content": "ok"}]


def test_safe_validate_blocks_converts_malformed_blocks_to_error_block() -> None:
    blocks = BlockService().safe_validate_blocks(
        [{"type": "table", "columns": ["name"]}],
        fallback_content="Summary",
    )

    assert blocks == [
        {
            "type": "error",
            "title": "Response block could not be displayed",
            "message": "Sherlock produced part of the response in an unsupported format.",
        }
    ]

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter


class MarkdownBlock(BaseModel):
    type: Literal["markdown"]
    content: str


class PlanBlock(BaseModel):
    type: Literal["plan"]
    steps: list[str]


class KpiBlock(BaseModel):
    type: Literal["kpi"]
    label: str
    value: str | int | float
    caption: str | None = None


class TableBlock(BaseModel):
    type: Literal["table"]
    columns: list[str]
    rows: list[dict[str, Any]]


class ChartBlock(BaseModel):
    type: Literal["chart"]
    title: str
    chart_type: str = "placeholder"
    data: list[dict[str, Any]] = Field(default_factory=list)


class QualityNoteBlock(BaseModel):
    type: Literal["quality_note"]
    severity: Literal["info", "warning", "critical"] = "info"
    title: str
    description: str


class SuggestionsBlock(BaseModel):
    type: Literal["suggestions"]
    suggestions: list[str]


class ErrorBlock(BaseModel):
    type: Literal["error"]
    title: str
    message: str


BlockAdapter = TypeAdapter(
    MarkdownBlock | PlanBlock | KpiBlock | TableBlock | ChartBlock | QualityNoteBlock | SuggestionsBlock | ErrorBlock
)


class BlockService:
    production_block_types = {"markdown", "plan", "kpi", "table", "chart", "quality_note", "suggestions", "error"}

    def validate_block(self, block: dict[str, Any]) -> dict[str, Any]:
        return BlockAdapter.validate_python(block).model_dump()

    def validate_blocks(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.validate_block(block) for block in blocks]

    def filter_for_environment(self, blocks: list[dict[str, Any]], app_env: str) -> list[dict[str, Any]]:
        if app_env != "production":
            return blocks
        return [block for block in blocks if block.get("type") in self.production_block_types]

    def build_blocks(
        self,
        *,
        content: str,
        rows: list[dict[str, Any]] | None = None,
        columns: list[str] | None = None,
        suggestions: list[str] | None = None,
        quality_note: dict[str, Any] | None = None,
        kpis: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = [{"type": "markdown", "content": content}]
        for kpi in kpis or []:
            blocks.append({"type": "kpi", **kpi})
        if rows is not None and columns is not None:
            blocks.append({"type": "table", "columns": columns, "rows": rows[:25]})
        if quality_note:
            blocks.append({"type": "quality_note", **quality_note})
        blocks.append(
            {
                "type": "suggestions",
                "suggestions": suggestions
                or [
                    "What columns have missing values?",
                    "Show a row count",
                    "Summarize this dataset",
                ],
            }
        )
        return self.validate_blocks(blocks)

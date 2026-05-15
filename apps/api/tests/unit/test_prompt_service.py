from __future__ import annotations

from app.agents.models import DatasetColumnContext, DatasetContext, DatasetQualityIssueContext
from app.services.prompt_service import PromptService


def test_prompts_include_bounded_memory_summary() -> None:
    service = PromptService()
    dataset = DatasetContext(
        id="dataset_1",
        name="Sales",
        physical_schema_name="user_data",
        physical_table_name="dataset_1",
        row_count=2,
        column_count=1,
        quality_status="good",
    )
    columns = [
        DatasetColumnContext(
            column_name="revenue",
            original_column_name="Revenue",
            column_index=0,
            postgres_type="numeric",
            semantic_type="numeric",
        )
    ]

    planner_prompt = service.build_planner_prompt(
        dataset=dataset,
        columns=columns,
        quality_issues=[],
        question="What changed?",
        memory_summary="assistant: West region was the prior focus.",
    )
    answer_prompt = service.build_answer_prompt(
        dataset=dataset,
        question="What changed?",
        query_summaries=[],
        quality_issues=[
            DatasetQualityIssueContext(
                issue_type="missing_values",
                severity="warning",
                title="Missing revenue",
                description="Revenue is missing in one row.",
            )
        ],
        memory_summary="assistant: West region was the prior focus.",
    )

    assert "Prior investigation context:" in planner_prompt
    assert "assistant: West region was the prior focus." in planner_prompt
    assert "assistant: West region was the prior focus." in answer_prompt
    assert "Relevant dataset quality caveats:" in answer_prompt
    assert "Missing revenue: Revenue is missing in one row." in answer_prompt

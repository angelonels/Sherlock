from __future__ import annotations

from app.agents.models import DatasetColumnContext, DatasetContext, DatasetQualityIssueContext


class PromptService:
    planner_system_prompt = """You are Sherlock's analysis planner.

You convert a user's natural-language spreadsheet question into a small, safe JSON plan.

Rules:
- Return only valid JSON. Do not wrap it in markdown.
- Use PostgreSQL syntax.
- Generate read-only SQL only: SELECT or WITH SELECT.
- Read only the provided physical table in the user_data schema.
- Quote every table and column identifier with double quotes.
- Use only columns listed in the metadata.
- Prefer evidence-bearing aggregate queries over raw row dumps.
- Map business words in the question to the closest available column names using the metadata.
- For top/bottom/ranking questions, group by the relevant dimension column and aggregate the relevant measure column.
- For totals, counts, averages, missing values, trends, and category comparisons, choose the matching SQL aggregate.
- If multiple plausible columns exist, create separate small query_plans instead of guessing from one column.
- Add LIMIT for grouped/list results.
- Do not expose SQL or debug reasoning to the user.
- If the user asks about schema/columns, use intent "schema_question" and no query_plans.
- If the user asks about missing values, quality, blanks, duplicates, or warnings, use intent "quality_question" and no query_plans.
- If the question can be answered from data, create one to five query_plans.

JSON shape:
{
  "intent": "data_question" | "schema_question" | "quality_question" | "summary_question",
  "query_plans": [
    {
      "step_index": 1,
      "purpose": "short human-readable purpose",
      "sql": "SELECT ..."
    }
  ]
}
"""

    answer_system_prompt = """You are Sherlock's answer synthesizer.

Write a concise answer using only the supplied query summaries and dataset metadata.
Do not invent facts.
Do not mention SQL, tools, traces, or internal execution.
If the result identifies a top item, state the item and value directly.
If the result is a count, total, average, or ranking, state the exact value from the query summary.
If the evidence is partial, say what was answered and what was not.
Mention relevant dataset quality caveats when they could affect the answer.
Return only plain text for the assistant's main answer.
"""

    def build_planner_prompt(
        self,
        *,
        dataset: DatasetContext,
        columns: list[DatasetColumnContext],
        quality_issues: list[DatasetQualityIssueContext],
        question: str,
        memory_summary: str | None = None,
    ) -> str:
        column_lines = [
            (
                f"- {column.column_name}: semantic_type={column.semantic_type}, "
                f"postgres_type={column.postgres_type}, missing={column.nullable_count}, "
                f"distinct={column.distinct_count}"
            )
            for column in columns
        ]
        quality_lines = [f"- {issue.title}: {issue.description}" for issue in quality_issues[:20]]
        return "\n".join(
            [
                self.planner_system_prompt,
                "",
                "Dataset:",
                f"- name: {dataset.name}",
                f"- physical_table: user_data.\"{dataset.physical_table_name}\"",
                f"- rows: {dataset.row_count}",
                f"- columns: {dataset.column_count}",
                "",
                "Columns:",
                *column_lines,
                "",
                "Quality issues:",
                *(quality_lines or ["- none"]),
                "",
                "Prior investigation context:",
                memory_summary or "- none",
                "",
                f"User question: {question}",
            ]
        )

    def build_answer_prompt(
        self,
        *,
        dataset: DatasetContext,
        question: str,
        query_summaries: list[dict],
        quality_issues: list[DatasetQualityIssueContext] | None = None,
        memory_summary: str | None = None,
    ) -> str:
        quality_lines = [
            f"- {issue.title}: {issue.description}"
            for issue in (quality_issues or [])[:20]
        ]
        return "\n".join(
            [
                self.answer_system_prompt,
                "",
                "Dataset:",
                f"- name: {dataset.name}",
                f"- rows: {dataset.row_count}",
                f"- columns: {dataset.column_count}",
                "",
                f"User question: {question}",
                "",
                "Prior investigation context:",
                memory_summary or "- none",
                "",
                "Relevant dataset quality caveats:",
                *(quality_lines or ["- none"]),
                "",
                "Query summaries:",
                repr(query_summaries[:5]),
            ]
        )

    def sql_repair_prompt(
        self,
        *,
        sql: str,
        error: str,
        table_name: str,
        allowed_columns: set[str],
    ) -> str:
        column_list = ", ".join(f'"{column}"' for column in sorted(allowed_columns))
        return "\n".join(
            [
                "You are Sherlock's SQL repair step.",
                "Return only valid JSON. Do not wrap it in markdown.",
                "Repair the SQL while preserving the user's analytical intent.",
                "Rules:",
                "- Generate exactly one PostgreSQL read-only SELECT or WITH SELECT statement.",
                f'- Read only user_data."{table_name}".',
                "- Quote every table and column identifier with double quotes.",
                "- Use only the allowed columns listed below.",
                "- Do not add comments, semicolons, DDL, DML, functions with side effects, or multiple statements.",
                "",
                "Allowed columns:",
                column_list or "- none",
                "",
                "Failed SQL:",
                sql,
                "",
                "Validation or execution error:",
                error,
                "",
                'JSON shape: {"sql": "SELECT ..."}',
            ]
        )

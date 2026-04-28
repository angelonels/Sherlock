from app.agents.models import QueryPlan


class SqlGenerationService:
    def row_count_plan(self, table_name: str) -> QueryPlan:
        return QueryPlan(step_index=1, purpose="Count dataset rows", sql=f'SELECT COUNT(*) AS row_count FROM user_data."{table_name}"')

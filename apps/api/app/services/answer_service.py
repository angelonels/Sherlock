from app.agents.models import QueryResultSummary


class AnswerService:
    def synthesize(self, question: str, summaries: list[QueryResultSummary]) -> str:
        if not summaries:
            return "I reviewed the dataset metadata."
        first = summaries[0]
        if first.rows:
            return f"Here is what I found for: {question}"
        return "I could not produce a data result for that question."

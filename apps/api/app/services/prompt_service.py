class PromptService:
    def sql_repair_prompt(self, sql: str, error: str) -> str:
        return f"Repair this read-only SQL safely.\nSQL: {sql}\nError: {error}"

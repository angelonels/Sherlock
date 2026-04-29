from app.agents.state import AnalystState


def load_context(state: AnalystState) -> AnalystState:
    return {**state}


def prepare_context(state: AnalystState) -> AnalystState:
    return {**state}


def classify_intent(state: AnalystState) -> AnalystState:
    question = state.get("user_question", "").lower()
    if "column" in question or "schema" in question:
        intent = "schema_question"
    elif "missing" in question or "quality" in question:
        intent = "quality_question"
    elif "summar" in question:
        intent = "summary_question"
    else:
        intent = "data_question"
    return {**state, "intent": intent}


def build_placeholder_blocks(state: AnalystState) -> AnalystState:
    return {**state, "blocks": [{"type": "markdown", "content": "I received your question. Analysis engine is connected."}]}


def persist_outputs(state: AnalystState) -> AnalystState:
    return {**state}

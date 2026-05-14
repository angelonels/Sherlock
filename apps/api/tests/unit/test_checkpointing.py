from app.agents.checkpointing import checkpoint_connection_string


def test_checkpoint_connection_string_removes_sqlalchemy_driver_name() -> None:
    assert checkpoint_connection_string(
        "postgresql+psycopg://user:pass@localhost:5432/sherlock"
    ) == "postgresql://user:pass@localhost:5432/sherlock"


def test_checkpoint_connection_string_preserves_native_postgres_url() -> None:
    url = "postgresql://user:pass@localhost:5432/sherlock"

    assert checkpoint_connection_string(url) == url

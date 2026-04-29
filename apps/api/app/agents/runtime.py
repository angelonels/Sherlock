from dataclasses import dataclass


@dataclass(frozen=True)
class GraphRuntime:
    thread_id: str
    checkpoint_ns: str
    durability: str = "sync"

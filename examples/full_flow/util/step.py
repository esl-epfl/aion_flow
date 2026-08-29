"""Flow step data model."""

from dataclasses import dataclass


@dataclass
class Step:
    name: str
    target: str
    variables: list[str]

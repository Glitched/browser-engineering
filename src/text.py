from dataclasses import dataclass


@dataclass(frozen=True)
class Text:
    text: str

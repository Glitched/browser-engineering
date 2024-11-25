import tkinter.font
from typing import Literal, NamedTuple, TypeAlias

Positioning: TypeAlias = Literal["normal", "superscript", "subscript"]


class PendingDisplayItem(NamedTuple):
    x: int
    text: str
    font: tkinter.font.Font
    positioning: Positioning


class DisplayItem(NamedTuple):
    x: int
    y: int
    text: str
    font: tkinter.font.Font

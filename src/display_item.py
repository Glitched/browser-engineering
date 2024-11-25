import tkinter.font
from typing import NamedTuple


class PendingDisplayItem(NamedTuple):
    x: int
    text: str
    font: tkinter.font.Font


class DisplayItem(NamedTuple):
    x: int
    y: int
    text: str
    font: tkinter.font.Font

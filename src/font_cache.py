import tkinter.font
from dataclasses import dataclass
from typing import Literal, TypeAlias

FontWeight: TypeAlias = Literal["normal", "bold"]
FontStyle: TypeAlias = Literal["roman", "italic"]


@dataclass(frozen=True)
class FontCacheEntry:
    size: int
    weight: FontWeight
    style: FontStyle


FONTS: dict[FontCacheEntry, tuple[tkinter.font.Font, tkinter.Label]] = {}


def get_font(size: int, weight: FontWeight, style: FontStyle):
    key = FontCacheEntry(size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

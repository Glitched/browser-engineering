from typing import Literal

from display_item import DisplayItem, PendingDisplayItem
from entities import entities
from font_cache import FontStyle, FontWeight, get_font
from tag import Tag
from text import Text

HSTEP, VSTEP = 13, 18


class Layout:
    tokens: list[Text | Tag]
    display_list: list[DisplayItem]
    line: list[PendingDisplayItem] = []
    cursor_x: int = HSTEP
    cursor_y: int = VSTEP
    size: int = 16
    weight: FontWeight = "normal"
    style: FontStyle = "roman"
    align: Literal["left", "center", "right"] = "left"

    def __init__(self, tokens: list[Text | Tag]):
        self.tokens = tokens

    def render(self, width: int):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP

        self.display_list = []
        self.line = []

        for t in self.tokens:
            self.token(t, width)
        self.flush(width)

        return self.display_list

    def token(self, t: Text | Tag, width: int):
        match t:
            case Text(text):
                for entity, replacement in entities.items():
                    text = text.replace(entity, replacement)
                for word in text.split():
                    self.word(word, width)
            case Tag(_):
                self.tag(t, width)

    def tag(self, tag: Tag, width: int):
        tag_name = tag.tag
        match tag_name.split()[0]:
            case "i":
                self.style = "italic"
            case "/i":
                self.style = "roman"
            case "b":
                self.weight = "bold"
            case "/b":
                self.weight = "normal"
            case "big":
                self.size += 4
            case "/big":
                self.size -= 4
            case "small":
                self.size -= 2
            case "/small":
                self.size += 2
            case "br" | "/br":
                self.flush(width)
            case "/p":
                self.flush(width)
                self.cursor_y += VSTEP
            case "h1":
                self.flush(width)
                self.size += 8
                if tag_name == 'h1 class="title"':
                    self.align = "center"
            case "/h1":
                self.flush(width)
                self.size -= 8
                self.align = "left"
                self.cursor_y += VSTEP
            case "h2":
                self.flush(width)
                self.size += 4
            case "/h2":
                self.flush(width)
                self.size -= 4
            case _:
                pass

    def word(self, word: str, width: int):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if self.cursor_x + w > width - HSTEP:
            self.flush(width)
        self.line.append(PendingDisplayItem(self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")

    def flush(self, width: int):
        if not self.line:
            return

        offset = 0
        if self.line:
            if self.align == "center":
                offset = (width - self.line[-1].x) // 2
            elif self.align == "right":
                offset = width - self.line[-1].x - HSTEP

        metrics = [item.font.metrics() for item in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + (max_ascent * 1.25)

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append(DisplayItem(x + offset, int(y), word, font))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = int(baseline + (max_descent * 1.25))
        self.cursor_x = HSTEP
        self.line = []

    def get_y_max(self):
        if len(self.display_list) == 0:
            return 1
        return self.display_list[-1].y

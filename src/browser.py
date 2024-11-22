import tkinter
from typing import TYPE_CHECKING

from entities import entities
from url import URL

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
PARAGRAPH_STEP = 2 * VSTEP

# Typeshed definitions require generics, but we can't subscript python builtins
if TYPE_CHECKING:
    EventType = tkinter.Event[tkinter.Misc]
else:
    EventType = tkinter.Event


class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas
    scroll: int
    display_list: list[tuple[int, int, str]]

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def load(self, url: URL):
        body = url.request()
        text = self.lex(body)
        self.layout(text)
        self.draw()

    def lex(self, body: str):
        output = ""
        in_tag = False
        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                output += c

        for entity, char in entities.items():
            output = output.replace(entity, char)

        return output

    def layout(self, text: str):
        display_list: list[tuple[int, int, str]] = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in text:
            # Support line breaks
            if c == "\n":
                cursor_x = HSTEP
                cursor_y += PARAGRAPH_STEP
                continue

            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x + HSTEP > WIDTH:
                cursor_x = HSTEP
                cursor_y += VSTEP

        self.display_list = display_list

    def draw(self):
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            # Skip drawing characters off screen
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue

            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e: EventType):
        SCROLL_STEP = 100
        self.scroll += SCROLL_STEP
        self.draw()

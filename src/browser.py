import tkinter
from typing import TYPE_CHECKING

from entities import entities
from url import URL

HSTEP, VSTEP = 13, 18
PARAGRAPH_STEP = 2 * VSTEP
SCROLL_STEP = 100

# Typeshed definitions require generics, but we can't subscript python builtins
if TYPE_CHECKING:
    EventType = tkinter.Event[tkinter.Misc]
else:
    EventType = tkinter.Event


class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas
    scroll: int
    text: str
    display_list: list[tuple[int, int, str]]
    width: int
    height: int

    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("Slama Browser")
        self.window.resizable(True, True)
        self.width = 800
        self.height = 600
        self.canvas = tkinter.Canvas(self.window, width=self.width, height=self.height)
        self.canvas.pack(expand=True, fill="both")
        self.scroll = 0
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<MouseWheel>", self.scrollwheel)
        self.window.bind("<Configure>", self.on_configure)

    def load(self, url: URL):
        body = url.request()
        text = self.lex(body)
        self.layout()
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

        self.text = output

    def layout(self):
        display_list: list[tuple[int, int, str]] = []
        cursor_x, cursor_y = HSTEP, VSTEP

        for c in self.text:
            # Support line breaks
            if c == "\n":
                cursor_x = HSTEP
                cursor_y += PARAGRAPH_STEP
                continue

            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x + HSTEP > self.width:
                cursor_x = HSTEP
                cursor_y += VSTEP

        self.display_list = display_list

    def draw(self):
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            # Skip drawing characters off screen
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue

            self.canvas.create_text(x, y - self.scroll, text=c)

    def on_configure(self, e: EventType):
        self.width = e.width
        self.height = e.height
        self.layout()
        self.draw()

    def add_scroll(self, offset: int):
        self.scroll = max(0, self.scroll + offset)

    def scrolldown(self, e: EventType):
        self.add_scroll(SCROLL_STEP)
        self.draw()

    def scrollup(self, e: EventType):
        self.add_scroll(-SCROLL_STEP)
        self.draw()

    def scrollwheel(self, e: EventType):
        self.add_scroll(e.delta * (SCROLL_STEP // 2))
        self.draw()

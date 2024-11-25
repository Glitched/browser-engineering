import tkinter
import tkinter.font
from typing import TYPE_CHECKING

from layout import Layout
from tag import Tag
from text import Text
from url import URL

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
SCROLL_BAR_WIDTH = 10


# Typeshed definitions require generics, but we can't subscript python builtins
if TYPE_CHECKING:
    EventType = tkinter.Event[tkinter.Misc]
else:
    EventType = tkinter.Event


class Browser:
    rtl: bool
    window: tkinter.Tk
    canvas: tkinter.Canvas
    scroll: int
    text: list[Text | Tag]
    width: int
    height: int
    fonts: dict[str, tkinter.font.Font]
    layout: Layout

    def __init__(self, rtl: bool = False):
        self.rtl = rtl
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
        self.lex(body)
        self.layout = Layout(self.text)
        self.layout.render(self.get_content_width())
        self.draw()

    def lex(self, body: str):
        out: list[Text | Tag] = []
        buffer = ""
        in_tag = False
        for c in body:
            if c == "<":
                in_tag = True
                if buffer:
                    out.append(Text(buffer))
                buffer = ""
            elif c == ">":
                in_tag = False
                out.append(Tag(buffer))
                buffer = ""
            else:
                buffer += c
        if not in_tag and buffer:
            out.append(Text(buffer))

        self.text = out

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, font in self.layout.display_list:
            # Skip drawing characters off screen
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue

            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor="nw")

        # Draw scroll bar
        y_max = self.layout.get_y_max()
        if y_max > self.height:
            bar = self.canvas.create_rectangle(
                self.width - SCROLL_BAR_WIDTH,
                (self.scroll / y_max) * self.height,
                self.width - 5,
                ((self.scroll + self.height) / y_max) * self.height,
            )
            self.canvas.itemconfig(bar, fill="#999999")

    def on_configure(self, e: EventType):
        # Not sure why we're getting a configure event with a width of 1 and height of 1
        if e.width < 100:
            return

        self.height = e.height
        if e.width != self.width:
            self.width = e.width
            self.layout.render(self.get_content_width())
        self.draw()

    def add_scroll(self, offset: int):
        self.scroll = min(max(0, self.scroll + offset), self.layout.get_y_max())

    def scrolldown(self, e: EventType):
        self.add_scroll(SCROLL_STEP)
        self.draw()

    def scrollup(self, e: EventType):
        self.add_scroll(-SCROLL_STEP)
        self.draw()

    def scrollwheel(self, e: EventType):
        self.add_scroll(e.delta * (SCROLL_STEP // 2))
        self.draw()

    def get_content_width(self):
        return self.width - SCROLL_BAR_WIDTH

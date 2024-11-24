import tkinter
import tkinter.font
from typing import TYPE_CHECKING

from entities import entities
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
    text: str
    display_list: list[tuple[int, int, str]]
    width: int
    height: int
    fonts: dict[str, tkinter.font.Font]

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
        self.fonts = {"helvetica": tkinter.font.Font(family="Helvetica", size=16)}

    def load(self, url: URL):
        body = url.request()
        self.lex(body)
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

        space = self.fonts["helvetica"].measure(" ")

        paragraphs = self.text.split("\n\n")
        for paragraph in paragraphs:
            for word in paragraph.split():
                w = self.fonts["helvetica"].measure(word)
                display_list.append((cursor_x, cursor_y, word))
                cursor_x += w + space
                if cursor_x + w > self.width - SCROLL_BAR_WIDTH:
                    cursor_x = HSTEP
                    cursor_y += int(self.fonts["helvetica"].metrics("linespace") * 1.25)

            cursor_x = HSTEP
            cursor_y += int(self.fonts["helvetica"].metrics("linespace") * 2.5)

        self.display_list = display_list

    def draw(self):
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            # Skip drawing characters off screen
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue

            self.canvas.create_text(
                x, y - self.scroll, text=c, font=self.fonts["helvetica"], anchor="nw"
            )

        # Draw scroll bar
        if self.get_y_max() > self.height:
            bar = self.canvas.create_rectangle(
                self.width - SCROLL_BAR_WIDTH,
                (self.scroll / self.get_y_max()) * self.height,
                self.width - 5,
                ((self.scroll + self.height) / self.get_y_max()) * self.height,
            )
            self.canvas.itemconfig(bar, fill="#999999")

    def get_y_max(self):
        if len(self.display_list) == 0:
            return 1
        return self.display_list[-1][1]

    def on_configure(self, e: EventType):
        self.width = e.width
        self.height = e.height
        self.layout()
        self.draw()

    def add_scroll(self, offset: int):
        self.scroll = min(max(0, self.scroll + offset), self.get_y_max())

    def scrolldown(self, e: EventType):
        self.add_scroll(SCROLL_STEP)
        self.draw()

    def scrollup(self, e: EventType):
        self.add_scroll(-SCROLL_STEP)
        self.draw()

    def scrollwheel(self, e: EventType):
        self.add_scroll(e.delta * (SCROLL_STEP // 2))
        self.draw()

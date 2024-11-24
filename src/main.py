import tkinter

from browser import Browser
from url import URL

if __name__ == "__main__":
    import sys

    match sys.argv:
        case [_, url]:
            Browser().load(URL(url))
        case [_, url, rtl]:
            if rtl == "--rtl":
                Browser(rtl=True).load(URL(url))
            else:
                Browser().load(URL(url))
        case _:
            Browser().load(
                URL("file:///Users/ryan/dev/browser-engineering/src/test.html")
            )

    tkinter.mainloop()

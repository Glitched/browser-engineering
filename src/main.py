import tkinter

from browser import Browser
from url import URL

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        Browser().load(URL("file:///Users/ryan/dev/browser-engineering/src/test.html"))
    else:
        Browser().load(URL(sys.argv[1]))

    tkinter.mainloop()

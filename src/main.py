from url import URL

entities = {
    "&lt;": "<",
    "&gt;": ">",
}


def show(body: str):
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

    print(output)


def load(url: URL):
    body = url.request()
    show(body)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        load(URL("file:///Users/ryan/dev/browser-engineering/src/test.html"))
    else:
        load(URL(sys.argv[1]))

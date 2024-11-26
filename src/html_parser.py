from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Element:
    tag: str
    parent: Element | None = None
    children: list[Element | Text] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)

    def __repr__(self):
        return (
            "<"
            + self.tag
            + " "
            + " ".join(f"{k}={v}" for k, v in self.attrs.items())
            + ">"
        )


@dataclass(frozen=True)
class Text:
    text: str
    parent: Element | None = None

    def __repr__(self):
        return repr(self.text)


class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def __init__(self, body: str):
        self.body = body
        self.unfinished: list[Element] = []

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text: str):
        # Ignore empty text nodes
        if text.isspace():
            return

        parent = self.unfinished[-1] if self.unfinished else None
        node = Text(text, parent)
        if parent:
            parent.children.append(node)

    def add_tag(self, tag: str):
        tag, attributes = self.get_attributes(tag)

        # Ignore DOCTYPE and comments
        if tag.startswith("!"):
            return

        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, parent, attrs=attributes)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, parent, attrs=attributes)
            self.unfinished.append(node)

    def get_attributes(self, text: str):
        parts = text.split()
        tag = parts[0].casefold()
        attributes: dict[str, str] = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def print_tree(self, node: Element | Text, indent: int = 0):
        print(" " * indent, node)
        match node:
            case Element():
                for child in node.children:
                    self.print_tree(child, indent + 2)
            case Text():
                pass
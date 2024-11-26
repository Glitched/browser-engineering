from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


@dataclass(frozen=True)
class Element:
    tag: str
    parent: Element | None = None
    children: list[HtmlNode] = field(default_factory=list)
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


@dataclass(frozen=True)
class Comment:
    text: str
    parent: Element | None = None

    def __repr__(self):
        return f"<!--{self.text}-->"


HtmlNode: TypeAlias = Element | Text | Comment


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

    HEAD_TAGS = [
        "base",
        "basefont",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
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

        self.implicit_tags(None)

        parent = self.unfinished[-1] if self.unfinished else None
        node = Text(text, parent)
        if parent:
            parent.children.append(node)

    def add_tag(self, text: str):
        tag, attributes = self.get_attributes(text)

        if tag == "!--":
            parent = self.unfinished[-1] if self.unfinished else None
            node = Comment(text[3:-3], parent)
            if parent:
                parent.children.append(node)
            return

        # Ignore DOCTYPE and comments
        if tag.startswith("!"):
            return

        self.implicit_tags(tag)

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
            # Don't allow directly nested paragraphs or list items
            if (
                self.unfinished
                and tag == self.unfinished[-1].tag
                and tag in ["p", "li"]
            ):
                node = self.unfinished.pop()
                self.unfinished[-1].children.append(node)

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
        if not self.unfinished:
            self.implicit_tags(None)

        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def print_tree(self, node: HtmlNode, indent: int = 0):
        print(" " * indent, node)
        match node:
            case Element():
                for child in node.children:
                    self.print_tree(child, indent + 2)
            case Text() | Comment():
                pass

    def implicit_tags(self, tag: str | None):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif (
                open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS
            ):
                self.add_tag("/head")
            else:
                break

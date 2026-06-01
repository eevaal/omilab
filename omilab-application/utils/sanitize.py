from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

ALLOWED_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "span",
    "strong",
    "u",
    "ul",
}
VOID_TAGS = {"br"}
ALLOWED_ATTRS = {
    "a": {"href", "title", "target", "rel"},
    "p": {"class"},
    "span": {"class"},
}
ALLOWED_CLASSES = {"ql-align-center", "ql-align-right", "ql-align-justify"}
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


class _HTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in ALLOWED_TAGS:
            return

        cleaned_attrs = self._clean_attrs(tag, attrs)
        attr_text = "".join(
            f' {name}="{escape(value, quote=True)}"' for name, value in cleaned_attrs
        )
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def _clean_attrs(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> list[tuple[str, str]]:
        allowed = ALLOWED_ATTRS.get(tag, set())
        cleaned: list[tuple[str, str]] = []

        for name, value in attrs:
            if value is None or name not in allowed:
                continue

            if name == "href":
                parsed = urlparse(value)
                if parsed.scheme and parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
                    continue

            if name == "target" and value != "_blank":
                continue

            if name == "rel":
                value = "noopener noreferrer"

            if name == "class":
                classes = [item for item in value.split() if item in ALLOWED_CLASSES]
                if not classes:
                    continue
                value = " ".join(classes)

            cleaned.append((name, value))

        if tag == "a" and any(name == "target" and value == "_blank" for name, value in cleaned):
            cleaned = [(name, value) for name, value in cleaned if name != "rel"]
            cleaned.append(("rel", "noopener noreferrer"))

        return cleaned

    def get_html(self) -> str:
        return "".join(self.parts)


def sanitize_html(value: str | None) -> str:
    if not value:
        return ""

    sanitizer = _HTMLSanitizer()
    sanitizer.feed(value)
    sanitizer.close()
    return sanitizer.get_html()

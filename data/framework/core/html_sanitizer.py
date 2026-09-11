"""
Whitelist-only HTML sanitizer for marketplace-ready descriptions
(BaseLinker/Allegro templates, etc).

Converts arbitrary scraped HTML into a strict subset:
  - Block tags kept: p, ul, ol, li, h2, h3 (headings normalized to h3)
  - Inline tags kept: b, strong, br
  - Zero attributes on any tag
  - No script/style/iframe/img/table/form/media — stripped entirely
  - <a>, <span>, <em>, <i>, <font> etc. are unwrapped (text kept, tag dropped)
  - <table> rows are converted to <ul><li>key: value</li></ul>
  - Defensive whitespace insertion at tag boundaries, since source HTML on
    many of these sites glues adjacent tags together with no whitespace
    (e.g. "</strong>to", "jak<strong>elewacje").

Shared across adapters that need a BaseLinker-safe description in addition
to (or instead of) the plain-text Product.description field.
"""
from __future__ import annotations

import html
import re

from bs4 import BeautifulSoup, NavigableString, Tag

_WS = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")
_NO_LEADING_SPACE = set(",.;:!?)]}%’'\"-–—")
_NO_TRAILING_SPACE_BEFORE = set("([{-–—/")
_DROP_ENTIRELY = {
    "script", "style", "iframe", "img", "noscript", "svg", "form",
    "input", "button", "object", "embed", "video", "audio", "picture",
}
_INLINE_KEEP = {"b", "strong", "br"}
_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_JUNK_PATTERNS = [
    "wykorzystujemy pliki cookie", "polityka prywatności", "zapisz się do newslettera",
    "pobierz karta charakterystyki", "pobierz zdjęcia produktów", "opis produktu pobierz",
    "facebook", "udostępnij", "skomentuj",
]


def _is_junk(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in _JUNK_PATTERNS)


def _last_visible_char(s: str) -> str:
    stripped = _TAG_RE.sub("", s)
    return stripped[-1] if stripped else ""


def _first_visible_char(s: str) -> str:
    stripped = _TAG_RE.sub("", s)
    return stripped[0] if stripped else ""


def render_inline(node) -> str:
    out: list[str] = []
    for child in getattr(node, "children", []):
        if isinstance(child, NavigableString):
            collapsed = _WS.sub(" ", str(child).replace("\xa0", " "))
            if collapsed.strip():
                out.append(html.escape(collapsed))
            elif collapsed:
                out.append(" ")
            continue
        name = getattr(child, "name", None)
        if name in _DROP_ENTIRELY:
            continue
        if name == "br":
            piece = "<br>"
        elif name in _INLINE_KEEP:
            inner = render_inline(child)
            piece = f"<{name}>{inner}</{name}>" if inner.strip() else ""
        else:
            # a, span, em, i, font, etc. — unwrap, keep text only (no external links)
            piece = render_inline(child)
        if piece:
            if out:
                prev_char = _last_visible_char(out[-1])
                next_char = _first_visible_char(piece)
                if (
                    prev_char and next_char
                    and not prev_char.isspace() and not next_char.isspace()
                    and next_char not in _NO_LEADING_SPACE
                    and prev_char not in _NO_TRAILING_SPACE_BEFORE
                ):
                    out.append(" ")
            out.append(piece)
    text = "".join(out)
    return re.sub(r"[ \t]{2,}", " ", text)


def _table_to_list(table: Tag) -> list[str]:
    items: list[str] = []
    for row in table.find_all("tr"):
        cols = row.find_all(["th", "td"])
        if len(cols) >= 2:
            key = render_inline(cols[0]).strip()
            val = render_inline(cols[1]).strip()
            if key and val:
                items.append(f"<li>{key}: {val}</li>")
        elif len(cols) == 1:
            val = render_inline(cols[0]).strip()
            if val:
                items.append(f"<li>{val}</li>")
    return [f"<ul>{''.join(items)}</ul>"] if items else []


def render_block(container) -> list[str]:
    parts: list[str] = []
    for child in container.children:
        if isinstance(child, NavigableString):
            text = _WS.sub(" ", str(child).replace("\xa0", " ")).strip()
            if text and not _is_junk(text):
                parts.append(f"<p>{html.escape(text)}</p>")
            continue
        name = child.name
        if name in _DROP_ENTIRELY:
            continue
        if name == "table":
            parts.extend(_table_to_list(child))
        elif name in _HEADINGS:
            inner = render_inline(child).strip()
            if inner and not _is_junk(inner):
                parts.append(f"<h3>{inner}</h3>")
        elif name == "p":
            inner = render_inline(child).strip()
            if inner and not _is_junk(inner):
                parts.append(f"<p>{inner}</p>")
        elif name in ("ul", "ol"):
            items = []
            for li in child.find_all("li", recursive=False):
                if li.find(["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "ul", "ol", "table"]):
                    parts.extend(render_block(li))
                    continue
                li_inner = render_inline(li).strip()
                if li_inner and not _is_junk(li_inner):
                    items.append(f"<li>{li_inner}</li>")
            if items:
                parts.append(f"<{name}>" + "".join(items) + f"</{name}>")
        elif name in ("div", "section", "span", "article", "font"):
            parts.extend(render_block(child))
        else:
            text = render_inline(child).strip()
            if text and len(text) > 3 and not _is_junk(text):
                parts.append(f"<p>{text}</p>")
    return parts


def build_description_html(container, exclude_classes: tuple[str, ...] = ()) -> str:
    """Render a BeautifulSoup container into safe whitelist-only HTML.

    exclude_classes: child elements matching any of these classes (checked
    via find_parent) are skipped entirely — use for embedded galleries,
    social widgets, etc. that sometimes live inside the description block.
    """
    if container is None:
        return ""
    soup = BeautifulSoup(str(container), "lxml")
    root = soup.find(container.name) or soup
    for cls in exclude_classes:
        for el in root.find_all(class_=cls):
            el.decompose()
    return "".join(render_block(root))

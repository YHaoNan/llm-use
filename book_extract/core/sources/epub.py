from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from book_extract.core.errors import DependencyError
from book_extract.core.models import ChapterRef, ConvertRequest, SourceConvertResult
from book_extract.core.sources.base import DocumentSource
from book_extract.core.workspace import OutputWorkspace


def _require_ebooklib():
    try:
        from ebooklib import epub  # type: ignore
        from ebooklib import ITEM_DOCUMENT, ITEM_IMAGE  # type: ignore
    except Exception as exc:
        raise DependencyError(
            "缺少依赖：ebooklib（用于解析 epub）",
            details={"package": "EbookLib", "import": "ebooklib"},
        ) from exc
    return epub, ITEM_DOCUMENT, ITEM_IMAGE


def _require_html_to_md():
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except Exception as exc:
        raise DependencyError(
            "缺少依赖：beautifulsoup4（用于解析 HTML）",
            details={"package": "beautifulsoup4", "import": "bs4"},
        ) from exc

    try:
        from markdownify import markdownify as _markdownify  # type: ignore
    except Exception as exc:
        raise DependencyError(
            "缺少依赖：markdownify（用于将 HTML 转换为 Markdown）",
            details={"package": "markdownify", "import": "markdownify"},
        ) from exc

    return BeautifulSoup, _markdownify


@dataclass(frozen=True)
class EpubHtmlToMarkdownOptions:
    heading_style: str = "ATX"
    strip: tuple[str, ...] = ("script", "style")


class EpubSource(DocumentSource):
    type = "epub"
    supported_extensions = (".epub",)

    def __init__(self, *, html_options: EpubHtmlToMarkdownOptions | None = None) -> None:
        self._html_options = html_options or EpubHtmlToMarkdownOptions()

    def convert(self, request: ConvertRequest, workspace: OutputWorkspace) -> SourceConvertResult:
        epub, ITEM_DOCUMENT, ITEM_IMAGE = _require_ebooklib()
        BeautifulSoup, markdownify = _require_html_to_md()

        book = epub.read_epub(str(request.input_path))

        image_items = {self._normalize_href(i.get_name()): i for i in book.get_items_of_type(ITEM_IMAGE)}
        chapters: list[ChapterRef] = []
        warnings: list[str] = []

        spine_ids = [s[0] if isinstance(s, tuple) else s for s in getattr(book, "spine", [])]
        if not spine_ids:
            doc_items = list(book.get_items_of_type(ITEM_DOCUMENT))
        else:
            doc_items = []
            for item_id in spine_ids:
                item = book.get_item_with_id(item_id)
                if item is None:
                    continue
                if item.get_type() == ITEM_DOCUMENT:
                    doc_items.append(item)

        for index, item in enumerate(doc_items, start=1):
            href = self._normalize_href(item.get_name())
            if self._should_skip_document(href):
                continue

            raw = item.get_content()
            html = self._decode_html(raw)
            soup = BeautifulSoup(html, "html.parser")
            for tag in self._html_options.strip:
                for node in soup.find_all(tag):
                    node.decompose()

            content_root = soup.body or soup

            self._rewrite_images(
                soup=content_root,
                base_href=href,
                image_items=image_items,
                workspace=workspace,
                warnings=warnings,
            )
            self._rewrite_links(soup=content_root, base_href=href)

            title = self._extract_title(content_root) or Path(href).stem
            slug = self._chapter_slug(index=index, href=href, title=title)
            markdown = markdownify(str(content_root), heading_style=self._html_options.heading_style).strip() + "\n"

            chapter = workspace.write_chapter(
                slug=slug,
                title=title,
                markdown=markdown,
                level=1,
                parent_id=None,
                source_ref={"href": href, "id": item.get_id()},
            )
            chapters.append(chapter)

        return SourceConvertResult(chapters=chapters, warnings=warnings, metadata={"spine_count": len(doc_items)})

    @staticmethod
    def _decode_html(content: bytes) -> str:
        for encoding in ("utf-8", "utf-16", "gb18030", "latin-1"):
            try:
                text = content.decode(encoding)
                return _strip_xml_decl(text)
            except Exception:
                continue
        return _strip_xml_decl(content.decode("utf-8", errors="replace"))

    @staticmethod
    def _normalize_href(href: str) -> str:
        return posixpath.normpath(href).lstrip("/")

    @staticmethod
    def _should_skip_document(href: str) -> bool:
        name = href.lower()
        if name.endswith("nav.xhtml") or name.endswith("nav.html"):
            return True
        if name.endswith("toc.xhtml") or name.endswith("toc.html"):
            return True
        return False

    @staticmethod
    def _extract_title(soup: Any) -> str | None:
        for h in soup.find_all(["h1", "h2", "h3"], limit=1):
            text = h.get_text(" ", strip=True)
            if text:
                return text
        title = soup.find("title")
        if title is not None:
            text = title.get_text(" ", strip=True)
            if text:
                return text
        return None

    @staticmethod
    def _chapter_slug(*, index: int, href: str, title: str) -> str:
        stem = Path(href).stem
        return f"{index:04d}-{stem}"

    @classmethod
    def _rewrite_links(cls, *, soup: Any, base_href: str) -> None:
        base_norm = cls._normalize_href(base_href)
        for a in soup.find_all("a"):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
                continue

            target, fragment = (href.split("#", 1) + [""])[:2]
            target = target.split("?", 1)[0]
            if not target:
                continue

            resolved = cls._normalize_href(posixpath.normpath(posixpath.join(posixpath.dirname(base_norm), target)))
            if resolved == base_norm and fragment:
                a["href"] = f"#{fragment}"

    @classmethod
    def _rewrite_images(
        cls,
        *,
        soup: Any,
        base_href: str,
        image_items: dict[str, Any],
        workspace: OutputWorkspace,
        warnings: list[str],
    ) -> None:
        base_dir = posixpath.dirname(base_href)
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue
            if src.startswith("data:") or src.startswith("http://") or src.startswith("https://"):
                continue

            clean = src.split("#", 1)[0].split("?", 1)[0]
            resolved = posixpath.normpath(posixpath.join(base_dir, clean)).lstrip("/")
            item = image_items.get(resolved)
            if item is None:
                warnings.append(f"missing_image:{resolved}")
                continue

            try:
                rel_path = workspace.write_image(
                    filename=posixpath.basename(resolved),
                    content=item.get_content(),
                    media_type=getattr(item, "media_type", None) or getattr(item, "get_media_type", lambda: None)(),
                )
                img["src"] = rel_path
            except Exception as exc:
                warnings.append(f"image_write_failed:{resolved}:{type(exc).__name__}")


_XML_DECL_RE = re.compile(r"^\s*<\?xml[^>]*\?>\s*", flags=re.IGNORECASE)
_XML_DECL_LOOSE_RE = re.compile(r"^\s*xml\s+version=['\"][^'\"]+['\"][^\n]*\n?", flags=re.IGNORECASE)


def _strip_xml_decl(text: str) -> str:
    cleaned = text.lstrip("\ufeff")
    cleaned = _XML_DECL_RE.sub("", cleaned)
    cleaned = _XML_DECL_LOOSE_RE.sub("", cleaned)
    return cleaned


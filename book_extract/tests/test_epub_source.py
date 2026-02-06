import tempfile
import unittest
from pathlib import Path

from book_extract import Converter, EpubSource, SourceRegistry


def _deps_available() -> bool:
    try:
        import ebooklib  # noqa: F401
        import bs4  # noqa: F401
        import markdownify  # noqa: F401
    except Exception:
        return False
    return True


@unittest.skipIf(not _deps_available(), "epub 依赖未安装（EbookLib/bs4/markdownify）")
class EpubSourceTests(unittest.TestCase):
    def test_epub_converts_html_and_extracts_images(self):
        from ebooklib import epub

        book = epub.EpubBook()
        book.set_identifier("id123")
        book.set_title("Test Book")
        book.set_language("en")

        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
        img_item = epub.EpubItem(uid="img1", file_name="images/img.png", media_type="image/png", content=img_bytes)
        book.add_item(img_item)

        c1 = epub.EpubHtml(title="Chapter 1", file_name="chap_01.xhtml", lang="en")
        c1.content = b"<html><body><h1>Chapter 1</h1><p>Hello</p><img src='images/img.png'/></body></html>"
        book.add_item(c1)

        book.spine = ["nav", c1]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / "book.epub"
            epub.write_epub(str(in_path), book)

            out_dir = Path(tmp) / "out"
            registry = SourceRegistry()
            registry.register(EpubSource())
            result = Converter(registry=registry).convert(input_path=in_path, output_dir=out_dir)

            self.assertTrue(result.index_path.exists())
            self.assertEqual(result.source_type, "epub")
            self.assertGreaterEqual(len(result.chapters), 1)

            chapter_path = out_dir / Path(result.chapters[0].path)
            md = chapter_path.read_text(encoding="utf-8")
            self.assertIn("Chapter 1", md)

            images = list((out_dir / "images").glob("*"))
            self.assertGreaterEqual(len(images), 1)
            self.assertIn("images/", md)


if __name__ == "__main__":
    unittest.main()


import json
import tempfile
import unittest
from pathlib import Path

from book_extract.core.converter import Converter
from book_extract.core.errors import OutputConflictError, UnsupportedFormatError
from book_extract.core.models import SourceConvertResult
from book_extract.core.registry import SourceRegistry
from book_extract.core.sources.base import DocumentSource


class DummyEpubSource(DocumentSource):
    type = "epub"
    supported_extensions = (".epub",)

    def convert(self, request, workspace):
        chapter = workspace.write_chapter(slug="chapter1", title="Chapter 1", markdown="# Chapter 1\n\nHello\n")
        return SourceConvertResult(chapters=[chapter])


class FrameworkTests(unittest.TestCase):
    def test_registry_selects_by_extension(self):
        registry = SourceRegistry()
        registry.register(DummyEpubSource())
        source = registry.get_for_path(Path("a/b/c/book.EPUB"))
        self.assertEqual(source.type, "epub")

    def test_unsupported_format_when_no_source_registered(self):
        converter = Converter(registry=SourceRegistry())
        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / "book.epub"
            in_path.write_bytes(b"")
            out_dir = Path(tmp) / "out"
            with self.assertRaises(UnsupportedFormatError):
                converter.convert(input_path=in_path, output_dir=out_dir)

    def test_convert_writes_index_and_chapter(self):
        registry = SourceRegistry()
        registry.register(DummyEpubSource())
        converter = Converter(registry=registry)

        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / "book.epub"
            in_path.write_bytes(b"")
            out_dir = Path(tmp) / "out"

            result = converter.convert(input_path=in_path, output_dir=out_dir)

            self.assertTrue((out_dir / "chapters").exists())
            self.assertTrue((out_dir / "images").exists())
            self.assertTrue(result.index_path.exists())
            self.assertEqual(len(result.chapters), 1)

            chapter_rel = result.chapters[0].path
            self.assertTrue((out_dir / Path(chapter_rel)).exists())

            payload = json.loads(result.index_path.read_text(encoding="utf-8"))
            self.assertIn("chapters", payload)
            self.assertEqual(len(payload["chapters"]), 1)
            self.assertNotIn("assets", payload)

    def test_output_conflict_when_dir_exists(self):
        registry = SourceRegistry()
        registry.register(DummyEpubSource())
        converter = Converter(registry=registry)

        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / "book.epub"
            in_path.write_bytes(b"")
            out_dir = Path(tmp) / "out"
            out_dir.mkdir(parents=True, exist_ok=True)

            with self.assertRaises(OutputConflictError):
                converter.convert(input_path=in_path, output_dir=out_dir)


if __name__ == "__main__":
    unittest.main()

import unittest

from book_extract.core.sources.epub import _strip_xml_decl


class XmlDeclStripTests(unittest.TestCase):
    def test_strip_standard_xml_decl(self):
        text = "<?xml version='1.0' encoding='utf-8'?>\n<html><body>x</body></html>"
        self.assertEqual(_strip_xml_decl(text), "<html><body>x</body></html>")

    def test_strip_bom_then_xml_decl(self):
        text = "\ufeff<?xml version='1.0' encoding='utf-8'?>\n<body>x</body>"
        self.assertEqual(_strip_xml_decl(text), "<body>x</body>")

    def test_strip_loose_xml_decl_text(self):
        text = "xml version='1.0' encoding='utf-8'?\n<body>x</body>"
        self.assertEqual(_strip_xml_decl(text), "<body>x</body>")


if __name__ == "__main__":
    unittest.main()

import unittest

from presentation import safe_csv_value, safe_html_text


class PresentationTests(unittest.TestCase):
    def test_escapes_html_tags_and_quotes(self):
        value = '<img src=x onerror="alert(1)">'
        self.assertEqual(
            safe_html_text(value),
            '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;',
        )

    def test_handles_none_and_plain_text(self):
        self.assertEqual(safe_html_text(None), "")
        self.assertEqual(safe_html_text("Maya Chen"), "Maya Chen")

    def test_csv_formula_prefixes_are_exported_as_text(self):
        for value in ("=HYPERLINK(\"https://example.com\")", "+1+1", "-1+1", "@SUM(A1:A2)", "  =1+1", "\t=1+1"):
            with self.subTest(value=value):
                self.assertEqual(safe_csv_value(value), "'" + value)

    def test_csv_plain_values_are_preserved(self):
        self.assertEqual(safe_csv_value("Maya Chen"), "Maya Chen")
        self.assertEqual(safe_csv_value("hello@example.test"), "hello@example.test")
        self.assertEqual(safe_csv_value(None), "")


if __name__ == "__main__":
    unittest.main()

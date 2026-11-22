import unittest

from presentation import safe_html_text


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


if __name__ == "__main__":
    unittest.main()

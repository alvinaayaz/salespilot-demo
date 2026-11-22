import unittest

from presentation import matches_lead_search, safe_csv_value, safe_html_text


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

    def test_lead_search_covers_contact_details_and_context(self):
        lead = {
            "name": "Jordan Lee", "company": "Northstar Digital",
            "role": "Founder", "source": "LinkedIn",
            "email": "jordan@example.com", "need": "Pipeline visibility",
            "notes": "Asked for a product walkthrough", "status": "Follow-up",
            "last_touch": "Imported",
        }
        for query in ("jordan@example.com", "founder", "linkedin", "walkthrough", "follow-up", "imported"):
            with self.subTest(query=query):
                self.assertTrue(matches_lead_search(lead, query))
        self.assertFalse(matches_lead_search(lead, "unrelated phrase"))

    def test_blank_search_matches_every_lead(self):
        self.assertTrue(matches_lead_search({"name": "Jordan"}, "  "))


if __name__ == "__main__":
    unittest.main()

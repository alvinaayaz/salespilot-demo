import unittest

from imports import parse_prospect_csv


class ProspectImportTests(unittest.TestCase):
    def test_parses_utf8_bom_and_common_column_aliases(self):
        data = (
            "\ufeffContact Name,Company Name,Interest,Job Title,Email,Pipeline Stage\n"
            "Jordan Lee,Northstar Digital,Needs lead tracking,Founder,jordan@example.com,Qualified\n"
        ).encode("utf-8")

        leads, errors = parse_prospect_csv(data)

        self.assertEqual(errors, [])
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["name"], "Jordan Lee")
        self.assertEqual(leads[0]["company"], "Northstar Digital")
        self.assertEqual(leads[0]["status"], "Qualified")
        self.assertEqual(leads[0]["source"], "Other")
        self.assertEqual(leads[0]["last_touch"], "Imported")

    def test_requires_core_columns(self):
        leads, errors = parse_prospect_csv(b"name,company\nJordan,Northstar\n")
        self.assertEqual(leads, [])
        self.assertIn("Contact name, Company, and Need", errors[0])

    def test_skips_existing_and_within_file_duplicates(self):
        data = (
            "name,company,need\n"
            "Jordan Lee,Northstar,Existing\n"
            "Maya Chen,Studio,New need\n"
            "maya chen,studio,Duplicate row\n"
        ).encode()
        leads, errors = parse_prospect_csv(
            data,
            [{"name": "Jordan Lee", "company": "Northstar"}],
        )
        self.assertEqual([lead["name"] for lead in leads], ["Maya Chen"])
        self.assertEqual(len(errors), 2)

    def test_rejects_invalid_email_and_stage(self):
        data = (
            "name,company,need,email,status\n"
            "Jordan,Northstar,Need,not-an-email,New\n"
            "Maya,Studio,Need,maya@example.com,Unknown\n"
        ).encode()
        leads, errors = parse_prospect_csv(data)
        self.assertEqual(leads, [])
        self.assertEqual(len(errors), 2)

    def test_rejects_non_utf8_and_oversized_files(self):
        self.assertIn("UTF-8", parse_prospect_csv(b"\xff")[1][0])
        self.assertIn("2 MB", parse_prospect_csv(b"x" * (2 * 1024 * 1024 + 1))[1][0])

    def test_skips_blank_rows_and_reports_missing_required_values(self):
        data = b"name,company,need\n,,,\nJordan,Northstar,\nMaya,Studio,Need\n"
        leads, errors = parse_prospect_csv(data)
        self.assertEqual([lead["name"] for lead in leads], ["Maya"])
        self.assertEqual(len(errors), 1)

    def test_rejects_duplicate_normalized_headers(self):
        data = b"name,Contact Name,company,need\nA,B,C,D\n"
        leads, errors = parse_prospect_csv(data)
        self.assertEqual(leads, [])
        self.assertIn("duplicate column", errors[0].lower())


if __name__ == "__main__":
    unittest.main()

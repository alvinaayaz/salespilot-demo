import unittest
from unittest.mock import patch

import storage


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table, select_rows=None):
        self.table = table
        self.select_rows = select_rows or []
        self.filters = []
        self.operation = "select"
        self.payload = None
        self.returning = False

    def select(self, *_args, **_kwargs):
        if self.operation == "update":
            self.returning = True
        else:
            self.operation = "select"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def execute(self):
        if self.operation == "select":
            return FakeResponse(self.select_rows)
        if self.operation == "insert":
            rows = self.payload if isinstance(self.payload, list) else [self.payload]
            return FakeResponse([{**row, "id": f"test-{i}"} for i, row in enumerate(rows)])
        return FakeResponse([{"id": "test-id"}] if self.returning else [])


class FakeClient:
    def __init__(self, select_rows=None):
        self.queries = []
        self.select_rows = select_rows or []

    def table(self, name):
        query = FakeQuery(name, self.select_rows)
        self.queries.append(query)
        return query


class StorageTests(unittest.TestCase):
    def test_load_seeds_only_with_current_user_id(self):
        client = FakeClient()
        leads = [{"name": "A", "company": "B", "need": "Need"}]

        result = storage.load_or_seed_leads(client, "user-123", leads)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "test-0")
        self.assertIn(("user_id", "user-123"), client.queries[0].filters)
        self.assertEqual(client.queries[1].payload[0]["user_id"], "user-123")

    def test_load_existing_leads_does_not_seed_again(self):
        existing = {
            "id": "lead-existing",
            "user_id": "user-123",
            "name": "Existing",
            "company": "Example Co",
            "need": "Need",
        }
        client = FakeClient(select_rows=[existing])

        result = storage.load_or_seed_leads(
            client,
            "user-123",
            [{"name": "Seed", "company": "Seed Co", "need": "Seed need"}],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "lead-existing")
        self.assertEqual(len(client.queries), 1)
        self.assertEqual(client.queries[0].filters, [("user_id", "user-123")])

    def test_load_empty_workspace_without_seed_stays_empty(self):
        client = FakeClient()

        result = storage.load_or_seed_leads(client, "user-empty", [])

        self.assertEqual(result, [])
        self.assertEqual(len(client.queries), 1)

    def test_insert_assigns_user_id_and_returns_database_id(self):
        client = FakeClient()
        result = storage.insert_lead(
            client,
            "user-456",
            {"name": "A", "company": "B", "need": "Need"},
        )

        self.assertEqual(result["id"], "test-0")
        self.assertEqual(client.queries[0].payload["user_id"], "user-456")

    def test_update_is_scoped_to_user_and_record(self):
        client = FakeClient()
        storage.update_lead(
            client,
            "user-789",
            {"id": "lead-1", "name": "A", "company": "B", "need": "Need"},
        )

        self.assertIn(("id", "lead-1"), client.queries[0].filters)
        self.assertIn(("user_id", "user-789"), client.queries[0].filters)
        self.assertTrue(client.queries[0].returning)


if __name__ == "__main__":
    unittest.main()

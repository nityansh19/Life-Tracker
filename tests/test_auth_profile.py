from types import SimpleNamespace
import unittest

from app.services.auth_service import AuthService


class _Result:
    def __init__(self, data=None):
        self.data = data


class _ProfileQuery:
    def __init__(self, client):
        self.client = client
        self.insert_payload = None

    def select(self, columns):
        self.client.calls.append(("select", columns))
        return self

    def eq(self, column, value):
        self.client.calls.append(("eq", column, value))
        return self

    def maybe_single(self):
        self.client.calls.append(("maybe_single",))
        return self

    def insert(self, payload):
        self.client.calls.append(("insert", payload))
        self.insert_payload = payload
        return self

    def upsert(self, *args, **kwargs):
        raise AssertionError("ensure_profile must not use upsert")

    def execute(self):
        if self.insert_payload is not None:
            self.client.profile = {
                **self.insert_payload,
                "created_at": "now",
                "updated_at": "now",
            }
            self.insert_payload = None
            return _Result(self.client.profile)
        return _Result(self.client.profile)


class _Client:
    def __init__(self, profile=None):
        self.profile = profile
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        self.assert_table = name
        return _ProfileQuery(self)


class AuthProfileTests(unittest.TestCase):
    def _service(self, profile=None):
        service = AuthService.__new__(AuthService)
        service.client = _Client(profile)
        service.user = SimpleNamespace(
            id="00000000-0000-0000-0000-000000000001",
            email="tester@example.com",
            user_metadata={"display_name": "Tester"},
        )
        return service

    def test_existing_profile_requires_no_write(self):
        existing = {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "display_name": "Tester",
            "plan": "free",
        }
        service = self._service(existing)
        result = service.ensure_profile()
        self.assertEqual(result["plan"], "free")
        self.assertFalse(any(call[0] == "insert" for call in service.client.calls))

    def test_missing_profile_uses_insert_not_upsert(self):
        service = self._service()
        result = service.ensure_profile()
        inserts = [call for call in service.client.calls if call[0] == "insert"]
        self.assertEqual(len(inserts), 1)
        self.assertEqual(inserts[0][1]["display_name"], "Tester")
        self.assertEqual(inserts[0][1]["plan"], "free")
        self.assertEqual(result["plan"], "free")


if __name__ == "__main__":
    unittest.main()

"""Synthetic offline tests only: no production data, network or Qdrant writes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import unittest

from gaia_rag_r05.authz import AccessDenied, AuthorizedScope, Authorizer, Principal, Scope
from gaia_rag_r05.scoped_reads import ScopedReads

ID = "11111111-1111-4111-8111-111111111111"
S_A1 = Scope("chatgpt", "DEMO-TENANT-A", "DEMO-A1")
S_A2 = Scope("chatgpt", "DEMO-TENANT-A", "DEMO-A2")
S_B = Scope("chatgpt", "DEMO-TENANT-B", "DEMO-B1")
ACTOR_A = Principal("demo-a@example.invalid", "https://team.cloudflareaccess.com", "DEMO-AUDIENCE")
ACTOR_B = Principal("demo-b@example.invalid", "https://team.cloudflareaccess.com", "DEMO-AUDIENCE")


def payload(scope=S_A1, **overrides):
    return dict(namespace=scope.namespace, tenant_id=scope.tenant_id,
                process_id=scope.process_id, approved=True,
                title="DEMO", text="Synthetic fixture", source_ref="DEMO-DOC", **overrides)


class FakeQdrant:
    def __init__(self):
        self.requests = []
        self.response = {"status": "ok", "result": {"points": []}}

    def __call__(self, method, path, data):
        self.requests.append((method, path, data))
        return self.response


class ScopedReadTests(unittest.TestCase):
    def setUp(self):
        self.grants = Authorizer({"demo-a@example.invalid": [S_A1, S_A2], "demo-b@example.invalid": [S_B]},
                                 expected_issuer="https://team.cloudflareaccess.com",
                                 expected_audience="DEMO-AUDIENCE")
        self.cap = self.grants.require(ACTOR_A, S_A1)
        self.q = FakeQdrant()
        self.reader = ScopedReads(self.q, "chatgpt_memoria_aprovada", "DEMO-model")

    def test_authorizer_denies_missing_principal(self):
        with self.assertRaises(AccessDenied):
            self.grants.require(None, S_A1)

    def test_cross_tenant_denied_before_network(self):
        with self.assertRaises(AccessDenied):
            self.grants.require(ACTOR_A, S_B)
        self.assertEqual(self.q.requests, [])

    def test_other_process_denied_before_network(self):
        with self.assertRaises(AccessDenied):
            self.grants.require(ACTOR_B, S_A1)
        self.assertEqual(self.q.requests, [])

    def test_wrong_jwt_issuer_denied(self):
        bad = Principal("demo-a@example.invalid", "https://other.cloudflareaccess.com", "DEMO-AUDIENCE")
        with self.assertRaises(AccessDenied):
            self.grants.require(bad, S_A1)

    def test_wrong_jwt_audience_denied(self):
        bad = Principal("demo-a@example.invalid", "https://team.cloudflareaccess.com", "OTHER-AUD")
        with self.assertRaises(AccessDenied):
            self.grants.require(bad, S_A1)

    def test_search_requires_four_server_filters(self):
        result = self.reader.search(self.cap, "DEMO legal issue")
        self.assertEqual(result, {"hits": []})
        conditions = self.q.requests[0][2]["filter"]["must"]
        self.assertEqual({c["key"]: c["match"]["value"] for c in conditions},
                         {"namespace": "chatgpt", "approved": True,
                          "tenant_id": "DEMO-TENANT-A", "process_id": "DEMO-A1"})

    def test_search_with_unexpected_tenant_fails_closed(self):
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "payload": payload(S_B)}]}}
        with self.assertRaises(AccessDenied):
            self.reader.search(self.cap, "DEMO")

    def test_missing_tenant_id_fails_closed(self):
        p = payload()
        del p["tenant_id"]
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "payload": p}]}}
        with self.assertRaises(AccessDenied):
            self.reader.search(self.cap, "DEMO")

    def test_approved_hit_returns(self):
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "score": .7, "payload": payload()}]}}
        self.assertEqual(self.reader.search(self.cap, "DEMO")["hits"][0]["id"], ID)

    def test_source_filter_is_not_global(self):
        self.reader.by_source(self.cap, "DEMO-DOC")
        conditions = self.q.requests[0][2]["filter"]["must"]
        self.assertEqual(conditions[-1], {"key": "source_ref", "match": {"value": "DEMO-DOC"}})
        self.assertEqual(len(conditions), 5)

    def test_uuid_rejects_other_tenant_without_content(self):
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "payload": payload(S_B)}]}}
        with self.assertRaises(AccessDenied):
            self.reader.by_uuid(self.cap, ID)

    def test_uuid_rejects_missing_tenant(self):
        p = payload(); p.pop("tenant_id")
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "payload": p}]}}
        with self.assertRaises(AccessDenied):
            self.reader.by_uuid(self.cap, ID)

    def test_uuid_rejects_invalid_id_before_request(self):
        with self.assertRaises(ValueError):
            self.reader.by_uuid(self.cap, "not-a-uuid")
        self.assertEqual(self.q.requests, [])

    def test_similar_only_same_tenant_authorized_processes(self):
        caps = self.grants.allowed_for_tenant(ACTOR_A, "chatgpt", "DEMO-TENANT-A")
        self.reader.similar(caps, "DEMO topic", "DEMO-A1")
        conditions = self.q.requests[0][2]["filter"]["must"]
        self.assertEqual(conditions[-1], {"key": "process_id", "match": {"any": ["DEMO-A2"]}})
        self.assertIn({"key": "tenant_id", "match": {"value": "DEMO-TENANT-A"}}, conditions)

    def test_similar_other_tenant_hit_rejected(self):
        caps = self.grants.allowed_for_tenant(ACTOR_A, "chatgpt", "DEMO-TENANT-A")
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "payload": payload(S_B)}]}}
        with self.assertRaises(AccessDenied):
            self.reader.similar(caps, "DEMO topic", "DEMO-A1")

    def test_similar_without_another_grant_does_not_call_backend(self):
        caps = (self.cap,)
        self.assertEqual(self.reader.similar(caps, "DEMO topic", "DEMO-A1"), {"similar": []})
        self.assertEqual(self.q.requests, [])

    def test_unapproved_never_returns(self):
        p = payload(); p["approved"] = False
        self.q.response = {"status": "ok", "result": {"points": [{"id": ID, "payload": p}]}}
        with self.assertRaises(AccessDenied):
            self.reader.search(self.cap, "DEMO")

    def test_backend_error_fails_closed(self):
        self.q.response = {"status": "error", "result": {"points": []}}
        with self.assertRaises(RuntimeError):
            self.reader.search(self.cap, "DEMO")

    def test_raw_scope_cannot_call_backend(self):
        with self.assertRaises(AccessDenied):
            self.reader.search(S_A1, "DEMO")
        self.assertEqual(self.q.requests, [])

    def test_global_namespace_only_is_not_grant(self):
        with self.assertRaises(AccessDenied):
            self.grants.require(ACTOR_A, Scope("chatgpt", "DEMO-TENANT-A", "DEMO-OTHER"))

    def test_non_dict_backend_result_denied(self):
        self.q.response = []
        with self.assertRaises(RuntimeError):
            self.reader.search(self.cap, "DEMO")

    def test_no_grant_returns_empty_denied(self):
        with self.assertRaises(AccessDenied):
            Authorizer({}, expected_issuer="https://team.cloudflareaccess.com",
                       expected_audience="DEMO-AUDIENCE").allowed_for_tenant(ACTOR_A, "chatgpt", "DEMO-TENANT-A")

    def test_forged_capability_denied_without_backend_call(self):
        forged = AuthorizedScope(ACTOR_A, S_A1)
        with self.assertRaises(AccessDenied):
            self.reader.search(forged, "DEMO")
        self.assertEqual(self.q.requests, [])

    def test_forged_capability_denied_in_similar(self):
        forged = AuthorizedScope(ACTOR_A, S_A2)
        with self.assertRaises(AccessDenied):
            self.reader.similar((self.cap, forged), "DEMO", "DEMO-A1")
        self.assertEqual(self.q.requests, [])

    def test_uuid_requires_backend_filter_for_tenant_process_and_id(self):
        self.assertEqual(self.reader.by_uuid(self.cap, ID), {"found": False})
        method, path, body = self.q.requests[0]
        self.assertEqual((method, path.endswith("/scroll")), ("POST", True))
        conditions = body["filter"]["must"]
        self.assertIn({"has_id": [ID]}, conditions)
        self.assertEqual(
            {c["key"]: c["match"]["value"] for c in conditions if "key" in c},
            {"namespace": "chatgpt", "approved": True,
             "tenant_id": "DEMO-TENANT-A", "process_id": "DEMO-A1"},
        )
        self.assertFalse(body["with_vector"])

    def test_uuid_authorized_result(self):
        self.q.response = {"status": "ok", "result": {"points": [
            {"id": ID, "payload": payload()}]}}
        value = self.reader.by_uuid(self.cap, ID)
        self.assertTrue(value["found"])
        self.assertEqual(value["item"]["id"], ID)

    def test_uuid_mismatched_response_id_denied(self):
        other = "22222222-2222-4222-8222-222222222222"
        self.q.response = {"status": "ok", "result": {"points": [
            {"id": other, "payload": payload()}]}}
        with self.assertRaises(AccessDenied):
            self.reader.by_uuid(self.cap, ID)

    def test_similar_requires_grant_for_current_process(self):
        caps = self.grants.allowed_for_tenant(ACTOR_A, "chatgpt", "DEMO-TENANT-A")
        with self.assertRaises(AccessDenied):
            self.reader.similar(caps, "DEMO", "DEMO-UNAUTHORIZED")
        self.assertEqual(self.q.requests, [])

    def test_backend_404_is_failure_not_empty_search(self):
        self.q.response = {"_http_status": 404, "status": "error"}
        with self.assertRaises(RuntimeError):
            self.reader.search(self.cap, "DEMO")

    def test_payload_does_not_override_point_identity(self):
        p = payload()
        p["id"] = "DEMO-SPOOFED-ID"
        p["score"] = -1
        self.q.response = {"status": "ok", "result": {"points": [
            {"id": ID, "score": 0.75, "payload": p}]}}
        item = self.reader.search(self.cap, "DEMO")["hits"][0]
        self.assertEqual(item["id"], ID)
        self.assertEqual(item["score"], 0.75)

    def test_source_cross_tenant_payload_denied(self):
        self.q.response = {"status": "ok", "result": {"points": [
            {"id": ID, "payload": payload(S_B)}]}}
        with self.assertRaises(AccessDenied):
            self.reader.by_source(self.cap, "DEMO-DOC")

    def test_list_process_applies_exact_process_filter(self):
        self.assertEqual(self.reader.list_process(self.cap), {"items": [], "next_offset": None})
        method, path, body = self.q.requests[0]
        self.assertEqual(method, "POST")
        self.assertTrue(path.endswith("/scroll"))
        conditions = body["filter"]["must"]
        self.assertEqual(
            {c["key"]: c["match"]["value"] for c in conditions},
            {"namespace": "chatgpt", "approved": True,
             "tenant_id": "DEMO-TENANT-A", "process_id": "DEMO-A1"},
        )

    def test_list_process_authorized_result(self):
        self.q.response = {"status": "ok", "result": {"points": [
            {"id": ID, "payload": payload()}], "next_page_offset": None}}
        items = self.reader.list_process(self.cap)["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], ID)

    def test_list_process_denies_cross_tenant_result(self):
        self.q.response = {"status": "ok", "result": {"points": [
            {"id": ID, "payload": payload(S_B)}]}}
        with self.assertRaises(AccessDenied):
            self.reader.list_process(self.cap)

    def test_list_process_rejects_invalid_offset_without_request(self):
        with self.assertRaises(ValueError):
            self.reader.list_process(self.cap, offset="DEMO-CROSS-TENANT")
        self.assertEqual(self.q.requests, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

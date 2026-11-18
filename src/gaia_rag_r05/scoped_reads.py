"""Read-only Qdrant adapter enforcing tenant and exact-process scope.

No live Qdrant requests are made by this module on import. Dependencies are
injected so tests use synthetic responses. Never add a namespace-only fallback.
"""
from __future__ import annotations

import re
import uuid
from typing import Callable

from .authz import AccessDenied, AuthorizedScope, require_issued_scope

QRequest = Callable[[str, str, dict | None], dict]
_COLLECTION = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class ScopedReads:
    def __init__(self, qrequest: QRequest, collection: str, model: str) -> None:
        if not _COLLECTION.fullmatch(collection) or not model or len(model) > 200:
            raise ValueError("INVALID_BACKEND_CONFIGURATION")
        self._request = qrequest
        self._base = f"/collections/{collection}/points"
        self._model = model

    @staticmethod
    def _scope(capability: AuthorizedScope) -> tuple[str, str, str]:
        s = require_issued_scope(capability)
        return s.namespace, s.tenant_id, s.process_id

    @staticmethod
    def _condition(key: str, value: str | bool) -> dict:
        return {"key": key, "match": {"value": value}}

    @classmethod
    def _filter(cls, capability: AuthorizedScope, *, source_ref: str = "") -> dict:
        namespace, tenant, process = cls._scope(capability)
        must = [cls._condition("namespace", namespace),
                cls._condition("approved", True),
                cls._condition("process_id", process)]
        if capability.access_mode != "owner":
            must.append(cls._condition("tenant_id", tenant))
        if source_ref:
            must.append(cls._condition("source_ref", source_ref))
        return {"must": must}

    @classmethod
    def _matches(cls, item: dict, capability: AuthorizedScope) -> bool:
        namespace, tenant, process = cls._scope(capability)
        return (item.get("approved") is True and item.get("namespace") == namespace
                and item.get("process_id") == process
                and (capability.access_mode == "owner" or item.get("tenant_id") == tenant))

    @staticmethod
    def _limit(limit: int, max_limit: int = 100) -> None:
        if type(limit) is not int or not 1 <= limit <= max_limit:
            raise ValueError("INVALID_LIMIT")

    @staticmethod
    def _result(res: dict, operation: str) -> dict | None:
        if not isinstance(res, dict):
            raise RuntimeError(operation + "_FAILED")
        if res.get("_http_status") == 404:
            raise RuntimeError(operation + "_FAILED")
        if res.get("status") != "ok" or not isinstance(res.get("result"), (dict, list)):
            raise RuntimeError(operation + "_FAILED")
        return res["result"]

    def search(self, capability: AuthorizedScope, query: str, limit: int = 8) -> dict:
        self._scope(capability)
        self._limit(limit, 20)
        if not isinstance(query, str) or not query.strip() or len(query) > 4000:
            raise ValueError("INVALID_QUERY")
        res = self._request("POST", self._base + "/query", {
            "query": {"text": query, "model": self._model}, "limit": limit,
            "with_payload": True, "filter": self._filter(capability)})
        result = self._result(res, "SEARCH")
        if result is None:
            return {"hits": []}
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list):
            raise RuntimeError("SEARCH_FAILED")
        hits = []
        for point in points:
            payload = point.get("payload") if isinstance(point, dict) else None
            if not isinstance(payload, dict) or not self._matches(payload, capability):
                raise AccessDenied("ACCESS_DENIED")
            hits.append({**payload, "id": point.get("id"), "score": point.get("score")})
        return {"hits": hits}

    def list_process(self, capability: AuthorizedScope, limit: int = 30,
                     offset: str | int | None = None) -> dict:
        """List only approved points in the exact authorized process."""
        self._scope(capability)
        self._limit(limit)
        if offset is not None:
            if type(offset) is int and offset >= 0:
                pass
            elif isinstance(offset, str):
                try:
                    offset = str(uuid.UUID(offset))
                except (ValueError, TypeError, AttributeError):
                    raise ValueError("INVALID_OFFSET") from None
            else:
                raise ValueError("INVALID_OFFSET")
        body = {
            "filter": self._filter(capability), "limit": limit,
            "with_payload": True, "with_vector": False,
        }
        if offset is not None:
            body["offset"] = offset
        result = self._result(self._request("POST", self._base + "/scroll", body), "SCROLL")
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list) or len(points) > limit:
            raise RuntimeError("SCROLL_FAILED")
        items = []
        for point in points:
            payload = point.get("payload") if isinstance(point, dict) else None
            if not isinstance(payload, dict) or not self._matches(payload, capability):
                raise AccessDenied("ACCESS_DENIED")
            items.append({**payload, "id": point.get("id")})
        next_offset = result.get("next_page_offset")
        if next_offset is not None:
            if type(next_offset) is int and next_offset >= 0:
                pass
            elif isinstance(next_offset, str):
                try:
                    next_offset = str(uuid.UUID(next_offset))
                except (ValueError, TypeError, AttributeError):
                    raise RuntimeError("SCROLL_FAILED") from None
            else:
                raise RuntimeError("SCROLL_FAILED")
        return {"items": items, "next_offset": next_offset}

    def by_source(self, capability: AuthorizedScope, source_ref: str, limit: int = 30) -> dict:
        self._scope(capability)
        self._limit(limit)
        if not isinstance(source_ref, str) or not source_ref.strip() or len(source_ref) > 300:
            raise ValueError("INVALID_SOURCE")
        res = self._request("POST", self._base + "/scroll", {
            "filter": self._filter(capability, source_ref=source_ref),
            "limit": limit, "with_payload": True, "with_vector": False})
        result = self._result(res, "SCROLL")
        if result is None:
            return {"items": [], "next_offset": None}
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list):
            raise RuntimeError("SCROLL_FAILED")
        items = []
        for point in points:
            payload = point.get("payload") if isinstance(point, dict) else None
            if not isinstance(payload, dict) or not self._matches(payload, capability):
                raise AccessDenied("ACCESS_DENIED")
            items.append({**payload, "id": point.get("id")})
        return {"items": items, "next_offset": result.get("next_page_offset")}

    def by_uuid(self, capability: AuthorizedScope, point_id: str) -> dict:
        # Enforce the tenant/process ACL INSIDE Qdrant, not only after a global
        # GET /points/{id}. Defense in depth: validate every returned payload.
        self._scope(capability)
        try:
            parsed_id = str(uuid.UUID(point_id))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("INVALID_POINT_ID") from None
        filt = self._filter(capability)
        filt["must"].append({"has_id": [parsed_id]})
        res = self._request("POST", self._base + "/scroll", {
            "filter": filt, "limit": 1,
            "with_payload": True, "with_vector": False})
        result = self._result(res, "SCROLL")
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list) or len(points) > 1:
            raise RuntimeError("SCROLL_FAILED")
        if not points:
            return {"found": False}
        point = points[0]
        payload = point.get("payload") if isinstance(point, dict) else None
        if not isinstance(payload, dict) or not self._matches(payload, capability):
            raise AccessDenied("ACCESS_DENIED")
        try:
            returned_id = str(uuid.UUID(str(point["id"])))
        except (KeyError, TypeError, ValueError, AttributeError):
            raise RuntimeError("SCROLL_FAILED") from None
        if returned_id != parsed_id:
            raise AccessDenied("ACCESS_DENIED")
        return {"found": True, "item": {**payload, "id": returned_id}}

    def similar(self, capabilities: tuple[AuthorizedScope, ...], query: str,
                current_process_id: str, limit: int = 8) -> dict:
        self._limit(limit, 20)
        if not capabilities or len(capabilities) > 32:
            raise AccessDenied("ACCESS_DENIED")
        base = self._scope(capabilities[0])
        principal = capabilities[0].principal
        for cap in capabilities:
            scope = self._scope(cap)
            if scope[:2] != base[:2] or cap.principal != principal:
                raise AccessDenied("ACCESS_DENIED")
        all_processes = {cap.scope.process_id for cap in capabilities}
        if current_process_id not in all_processes:
            raise AccessDenied("ACCESS_DENIED")
        authorized = {cap.scope.process_id: cap for cap in capabilities
                      if cap.scope.process_id != current_process_id}
        if not authorized:
            return {"similar": []}
        if not isinstance(query, str) or not query.strip() or len(query) > 4000:
            raise ValueError("INVALID_QUERY")
        namespace, tenant, _ = base
        filt = {"must": [self._condition("namespace", namespace),
                         self._condition("tenant_id", tenant),
                         self._condition("approved", True),
                         {"key": "process_id", "match": {"any": sorted(authorized)}}]}
        res = self._request("POST", self._base + "/query", {
            "query": {"text": query, "model": self._model}, "limit": limit,
            "with_payload": True, "filter": filt})
        result = self._result(res, "SEARCH")
        if result is None:
            return {"similar": []}
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list):
            raise RuntimeError("SEARCH_FAILED")
        hits = []
        for point in points:
            payload = point.get("payload") if isinstance(point, dict) else None
            cap = authorized.get(payload.get("process_id")) if isinstance(payload, dict) else None
            if cap is None or not self._matches(payload, cap):
                raise AccessDenied("ACCESS_DENIED")
            hits.append({"id": point.get("id"), "score": point.get("score"), **payload})
        return {"similar": hits}

    @staticmethod
    def _owner(capability: AuthorizedScope) -> tuple[str, str]:
        scope = require_issued_scope(capability)
        if capability.access_mode != "owner" or scope.tenant_id != "owner-all":
            raise AccessDenied("ACCESS_DENIED")
        return scope.namespace, scope.process_id

    def search_all_owner(self, capability: AuthorizedScope, query: str, limit: int = 8) -> dict:
        """Search all approved GAIA memory, including older points without tenant tags."""
        namespace, _ = self._owner(capability)
        self._limit(limit, 20)
        if not isinstance(query, str) or not query.strip() or len(query) > 4000:
            raise ValueError("INVALID_QUERY")
        filt = {"must": [self._condition("namespace", namespace),
                         self._condition("approved", True)]}
        res = self._request("POST", self._base + "/query", {
            "query": {"text": query, "model": self._model}, "limit": limit,
            "with_payload": True, "filter": filt})
        result = self._result(res, "SEARCH")
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list):
            raise RuntimeError("SEARCH_FAILED")
        hits = []
        for point in points:
            payload = point.get("payload") if isinstance(point, dict) else None
            if (not isinstance(payload, dict) or payload.get("approved") is not True
                    or payload.get("namespace") != namespace):
                raise AccessDenied("ACCESS_DENIED")
            hits.append({**payload, "id": point.get("id"), "score": point.get("score")})
        return {"hits": hits}

    def similar_owner(self, capability: AuthorizedScope, query: str, limit: int = 8) -> dict:
        """Cross-client comparable cases, never relying on a client's ACL."""
        namespace, current_process_id = self._owner(capability)
        self._limit(limit, 20)
        if not isinstance(query, str) or not query.strip() or len(query) > 4000:
            raise ValueError("INVALID_QUERY")
        filt = {"must": [self._condition("namespace", namespace),
                         self._condition("approved", True)],
                "must_not": [self._condition("process_id", current_process_id)]}
        res = self._request("POST", self._base + "/query", {
            "query": {"text": query, "model": self._model}, "limit": limit,
            "with_payload": True, "filter": filt})
        result = self._result(res, "SEARCH")
        points = result.get("points") if isinstance(result, dict) else None
        if not isinstance(points, list):
            raise RuntimeError("SEARCH_FAILED")
        hits = []
        for point in points:
            payload = point.get("payload") if isinstance(point, dict) else None
            if (not isinstance(payload, dict) or payload.get("approved") is not True
                    or payload.get("namespace") != namespace
                    or not isinstance(payload.get("process_id"), str)
                    or payload["process_id"] == current_process_id):
                raise AccessDenied("ACCESS_DENIED")
            hits.append({"id": point.get("id"), "score": point.get("score"), **payload})
        return {"similar": hits}

"""Read-only Qdrant adapter enforcing tenant and exact-process scope.

No live Qdrant requests are made by this module on import. Dependencies are
injected so tests use synthetic responses. Never add a namespace-only fallback.
"""
from __future__ import annotations

import re
import uuid
from typing import Callable

from .authz import AccessDenied, AuthorizedScope

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
        if not isinstance(capability, AuthorizedScope):
            raise AccessDenied("ACCESS_DENIED")
        s = capability.scope
        return s.namespace, s.tenant_id, s.process_id

    @staticmethod
    def _condition(key: str, value: str | bool) -> dict:
        return {"key": key, "match": {"value": value}}

    @classmethod
    def _filter(cls, capability: AuthorizedScope, *, source_ref: str = "") -> dict:
        namespace, tenant, process = cls._scope(capability)
        must = [cls._condition("namespace", namespace),
                cls._condition("approved", True),
                cls._condition("tenant_id", tenant),
                cls._condition("process_id", process)]
        if source_ref:
            must.append(cls._condition("source_ref", source_ref))
        return {"must": must}

    @classmethod
    def _matches(cls, item: dict, capability: AuthorizedScope) -> bool:
        namespace, tenant, process = cls._scope(capability)
        return (item.get("approved") is True and item.get("namespace") == namespace
                and item.get("tenant_id") == tenant and item.get("process_id") == process)

    @staticmethod
    def _limit(limit: int, max_limit: int = 100) -> None:
        if type(limit) is not int or not 1 <= limit <= max_limit:
            raise ValueError("INVALID_LIMIT")

    @staticmethod
    def _result(res: dict, operation: str) -> dict | None:
        if not isinstance(res, dict):
            raise RuntimeError(operation + "_FAILED")
        if res.get("_http_status") == 404:
            return None
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
            hits.append({"id": point.get("id"), "score": point.get("score"), **payload})
        return {"hits": hits}

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
        # Authorization happens before retrieval; object scope is checked again
        # BEFORE any payload is returned to the MCP consumer.
        self._scope(capability)
        try:
            parsed_id = str(uuid.UUID(point_id))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("INVALID_POINT_ID") from None
        res = self._request("GET", self._base + "/" + parsed_id, None)
        result = self._result(res, "GET")
        if result is None:
            return {"found": False}
        payload = result.get("payload") if isinstance(result, dict) else None
        if not isinstance(payload, dict) or not self._matches(payload, capability):
            return {"found": False}
        return {"found": True, "item": {**payload, "id": result.get("id")}}

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

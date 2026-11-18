"""Fail-closed per-process authorization independent of MCP/Qdrant transport.

Only a trusted Cloudflare Access JWT verification layer may create a Principal.
Grants must originate in a server-owned authoritative registry, never MCP tool
arguments or Qdrant payload. No grants and no verified principal => deny.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]{1,150}$")
_SUBJECT = re.compile(r"^[A-Za-z0-9_.:@+-]{1,200}$")


class AccessDenied(PermissionError):
    """Public exception must never contain another tenant's identifiers."""


def _identifier(value: str) -> bool:
    return isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value))


@dataclass(frozen=True, slots=True)
class Principal:
    """Identity created only after signed Cloudflare Access JWT validation."""

    subject: str
    verified_issuer: str
    verified_audience: str

    def __post_init__(self) -> None:
        if not isinstance(self.subject, str) or not _SUBJECT.fullmatch(self.subject) or not _identifier(self.verified_audience):
            raise AccessDenied("ACCESS_DENIED")
        if not isinstance(self.verified_issuer, str) or not self.verified_issuer.startswith("https://"):
            raise AccessDenied("ACCESS_DENIED")


@dataclass(frozen=True, slots=True)
class Scope:
    namespace: str
    tenant_id: str
    process_id: str

    def __post_init__(self) -> None:
        if not all(_identifier(x) for x in (self.namespace, self.tenant_id, self.process_id)):
            raise AccessDenied("ACCESS_DENIED")


@dataclass(frozen=True, slots=True)
class AuthorizedScope:
    """Capability issued by Authorizer; never construct from tool arguments."""

    principal: Principal
    scope: Scope


class Authorizer:
    def __init__(self, trusted_grants: Mapping[str, Iterable[Scope]], *,
                 expected_issuer: str, expected_audience: str) -> None:
        """Read-only snapshot from a trusted ACL registry, not user input."""
        if not expected_issuer.startswith("https://") or not _identifier(expected_audience):
            raise ValueError("INVALID_EXPECTED_IDENTITY")
        self._issuer = expected_issuer.rstrip("/")
        self._audience = expected_audience
        self._grants: dict[str, frozenset[Scope]] = {}
        for subject, scopes in trusted_grants.items():
            if not isinstance(subject, str) or not _SUBJECT.fullmatch(subject):
                raise ValueError("INVALID_ACL_SUBJECT")
            entries = frozenset(scopes)
            if not all(isinstance(s, Scope) for s in entries):
                raise ValueError("INVALID_ACL_ENTRY")
            self._grants[subject] = entries

    def require(self, principal: Principal | None, requested: Scope) -> AuthorizedScope:
        if not isinstance(principal, Principal) or not isinstance(requested, Scope):
            raise AccessDenied("ACCESS_DENIED")
        if (principal.verified_issuer != self._issuer
                or principal.verified_audience != self._audience
                or requested not in self._grants.get(principal.subject, frozenset())):
            raise AccessDenied("ACCESS_DENIED")
        return AuthorizedScope(principal, requested)

    def allowed_for_tenant(self, principal: Principal | None, namespace: str,
                           tenant_id: str) -> tuple[AuthorizedScope, ...]:
        if (not isinstance(principal, Principal) or not _identifier(namespace)
                or not _identifier(tenant_id) or principal.verified_issuer != self._issuer
                or principal.verified_audience != self._audience):
            raise AccessDenied("ACCESS_DENIED")
        matches = sorted((s for s in self._grants.get(principal.subject, frozenset())
                          if s.namespace == namespace and s.tenant_id == tenant_id),
                         key=lambda s: s.process_id)
        if not matches or len(matches) > 32:
            raise AccessDenied("ACCESS_DENIED")
        return tuple(AuthorizedScope(principal, s) for s in matches)

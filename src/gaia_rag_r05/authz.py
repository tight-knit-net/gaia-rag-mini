"""Fail-closed per-process authorization independent of MCP/Qdrant transport.

Only a trusted Cloudflare Access JWT verification layer may create a Principal.
Grants must originate in a server-owned authoritative registry, never MCP tool
arguments or Qdrant payload. No grants and no verified principal => deny.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping
from weakref import WeakSet

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


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class AuthorizedScope:
    """Opaque, identity-based capability issued by Authorizer.

    Calling the public constructor alone does not grant access. Only objects
    recorded by Authorizer in this process are accepted by ScopedReads.
    """

    principal: Principal
    scope: Scope
    access_mode: str = "process"


_ISSUED_SCOPES: WeakSet[AuthorizedScope] = WeakSet()


def require_issued_scope(capability: object) -> Scope:
    """Reject hand-crafted capability objects before any backend read."""
    if not isinstance(capability, AuthorizedScope) or capability not in _ISSUED_SCOPES:
        raise AccessDenied("ACCESS_DENIED")
    return capability.scope


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

    @staticmethod
    def _issue(principal: Principal, scope: Scope, *, access_mode: str = "process") -> AuthorizedScope:
        capability = AuthorizedScope(principal, scope, access_mode=access_mode)
        _ISSUED_SCOPES.add(capability)
        return capability

    def require(self, principal: Principal | None, requested: Scope) -> AuthorizedScope:
        if not isinstance(principal, Principal) or not isinstance(requested, Scope):
            raise AccessDenied("ACCESS_DENIED")
        if (principal.verified_issuer != self._issuer
                or principal.verified_audience != self._audience
                or requested not in self._grants.get(principal.subject, frozenset())):
            raise AccessDenied("ACCESS_DENIED")
        return self._issue(principal, requested)

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
        return tuple(self._issue(principal, s) for s in matches)


class OwnerAuthorizer(Authorizer):
    """Authenticated GAIA owner can read every approved process across clients.

    Scope is a process locator, NOT a per-client permission. Owner identity still
    requires verified Cloudflare Access JWT and explicit server-owned allowlist.
    """

    def __init__(self, trusted_owners: Iterable[str], *,
                 expected_issuer: str, expected_audience: str) -> None:
        super().__init__({}, expected_issuer=expected_issuer, expected_audience=expected_audience)
        owners = tuple(trusted_owners)
        if not owners or len(owners) > 64 or any(
                not isinstance(v, str) or not _SUBJECT.fullmatch(v)
                or v != v.lower() for v in owners):
            raise ValueError("INVALID_OWNER_REGISTRY")
        self._owners = frozenset(owners)

    def require(self, principal: Principal | None, requested: Scope) -> AuthorizedScope:
        if (not isinstance(principal, Principal) or not isinstance(requested, Scope)
                or principal.verified_issuer != self._issuer
                or principal.verified_audience != self._audience
                or principal.subject not in self._owners
                or requested.tenant_id != "owner-all"):
            raise AccessDenied("ACCESS_DENIED")
        return self._issue(principal, requested, access_mode="owner")

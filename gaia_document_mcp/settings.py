"""Fail-closed feature configuration; never read or log secret values."""
from __future__ import annotations
from dataclasses import dataclass
import os

def is_explicitly_enabled(name: str, env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return values.get(name, "0") == "1"

@dataclass(frozen=True)
class GateSettings:
    real_documents: bool = False
    external_llm: bool = False
    google_writes: bool = False
    signatures: bool = False
    memory_writes: bool = False

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "GateSettings":
        return cls(
            real_documents=is_explicitly_enabled("GAIA_DOC_REAL_DOCUMENTS", env),
            external_llm=is_explicitly_enabled("GAIA_DOC_EXTERNAL_LLM", env),
            google_writes=is_explicitly_enabled("GAIA_DOC_GOOGLE_WRITES", env),
            signatures=is_explicitly_enabled("GAIA_DOC_SIGNATURES", env),
            memory_writes=is_explicitly_enabled("GAIA_DOC_MEMORY_WRITES", env),
        )

    def may_execute(self, capability: str) -> bool:
        flags = {
            "inspect_synthetic": True,
            "real_document": self.real_documents,
            "external_llm": self.external_llm and self.real_documents,
            "google_write": self.google_writes and self.real_documents,
            "signature": self.signatures and self.real_documents,
            # Never permit writing Qdrant via this project, even if an env is set.
            "direct_qdrant_write": False,
        }
        return flags.get(capability, False)


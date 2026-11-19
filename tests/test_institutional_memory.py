"""R07 offline tests: fictional administrative memory; no network or writes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05.institutional_memory import preview

P = "DEMO-PROCESSO-001"
OLD = "11111111-1111-4111-8111-111111111111"


def memory(**kwargs):
    item = {
        "id": OLD, "approved": True, "process_id": P,
        "title": "Conferir evidência antes do protocolo",
        "text": "Exigência foi identificada. Protocolo ainda não comprovado.",
        "source_ref": "DEMO-SOURCE-A",
    }
    item.update(kwargs)
    return item


def candidate(**kwargs):
    data = dict(
        process_id=P,
        title="Conferir evidência antes do protocolo",
        summary="Novo checklist institucional de evidências.",
        source_ref="DEMO-SOURCE-B",
        kind="procedimento",
        evidence_status="documentada",
        previous=[],
        coverage_complete=True,
    )
    data.update(kwargs)
    return preview(**data)


class InstitutionalMemoryTests(unittest.TestCase):
    def test_new_candidate_requires_two_approvals(self):
        r = candidate()
        self.assertEqual(r["disposition"], "NOVA_CANDIDATA")
        self.assertTrue(r["document_approval_required"])
        self.assertTrue(r["human_memory_approval_required"])
        self.assertFalse(r["persisted"])
        self.assertTrue(r["old_points_unchanged"])

    def test_duplicates_are_not_promoted(self):
        r = candidate(
            summary="  exigência foi identificada.   PROTOCOLO AINDA NÃO comprovado. ",
            previous=[memory()],
        )
        self.assertEqual(r["disposition"], "DUPLICATA_NAO_PROPOR")
        self.assertEqual(r["exact_duplicates"][0]["point_id"], OLD)
        self.assertIn("DUPLICIDADE_IDENTIFICADA", r["blockers"])

    def test_same_source_revision_proposed_but_not_applied(self):
        r = candidate(source_ref="DEMO-SOURCE-A", previous=[memory()])
        self.assertEqual(r["disposition"], "REVISAO_CANDIDATA")
        self.assertEqual(r["same_source_revisions"][0]["point_id"], OLD)
        self.assertTrue(r["old_points_unchanged"])

    def test_explicit_prior_references_approved_same_process(self):
        r = candidate(prior_point_id=OLD, previous=[memory()])
        self.assertTrue(r["prior_verified"])
        self.assertEqual(r["disposition"], "REVISAO_CANDIDATA")

    def test_wrong_process_source_is_rejected_even_if_owner_wide(self):
        with self.assertRaisesRegex(ValueError, "PREVIOUS_SCOPE_UNVERIFIED"):
            candidate(previous=[memory(process_id="DEMO-OTHER-CASE")])

    def test_unapproved_memory_rejected_from_context(self):
        with self.assertRaisesRegex(ValueError, "PREVIOUS_SCOPE_UNVERIFIED"):
            candidate(previous=[memory(approved=False)])

    def test_simulation_is_not_real_precedent(self):
        r = candidate(kind="simulacao", evidence_status="simulada")
        self.assertEqual(r["disposition"], "EXEMPLO_NAO_PROMOVER")
        self.assertIn("SIMULACAO_NAO_E_PRECEDENTE_REAL", r["blockers"])

    def test_allegation_never_becomes_proven_fact(self):
        r = candidate(evidence_status="alegada")
        self.assertIn("EVIDENCIA_INSUFICIENTE_PARA_FATO", r["blockers"])

    def test_related_title_is_not_proof_of_supersession(self):
        r = candidate(previous=[memory()])
        self.assertEqual(r["disposition"], "RELACAO_A_VERIFICAR")
        self.assertEqual(r["related_titles"][0]["point_id"], OLD)

    def test_missing_prior_with_complete_index_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "PRIOR_NOT_FOUND_IN_PROCESS"):
            candidate(
                previous=[memory()],
                prior_point_id="22222222-2222-4222-8222-222222222222",
            )

    def test_incomplete_index_does_not_claim_prior_missing(self):
        r = candidate(
            previous=[memory()],
            prior_point_id="22222222-2222-4222-8222-222222222222",
            coverage_complete=False,
        )
        self.assertIn("MEMORIA_ANTERIOR_NAO_VERIFICADA", r["blockers"])
        self.assertIn("COBERTURA_PARCIAL_DO_HISTORICO", r["blockers"])

    def test_invalid_id_and_category_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_PRIOR_POINT_ID"):
            candidate(prior_point_id="not-uuid")
        with self.assertRaisesRegex(ValueError, "INVALID_MEMORY_KIND"):
            candidate(kind="deferimento_automatico")

    def test_invalid_or_empty_evidence_and_source(self):
        with self.assertRaisesRegex(ValueError, "INVALID_EVIDENCE_STATUS"):
            candidate(evidence_status="confirmada_pela_IA")
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_REF"):
            candidate(source_ref=" ")

    def test_source_does_not_overwrite_old_point(self):
        previous = [memory()]
        before = dict(previous[0])
        candidate(source_ref="DEMO-SOURCE-A", previous=previous)
        self.assertEqual(previous[0], before)


if __name__ == "__main__":
    unittest.main()

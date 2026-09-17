"""
Unit Test for Interactive Human-in-the-Loop (HITL) Adjudication Gate.
Verifies start_audit, interrupt payload, claim overrides, dynamic triggers, and resume_audit.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.extractor import build_product_input
from src.hitl import NutriAuditHITLGraph
from src.schemas import ClaimAdjudication, HITLAdjudicationPayload


def test_hitl_adjudication():
    print("=== Testing Interactive HITL Adjudication Gate ===")
    db_path = os.path.join("data", "test_hitl_adj.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    graph = NutriAuditHITLGraph(db_path=db_path)
    
    # Create test product with a known violation (100% Atta claim with Maida > Atta)
    product = build_product_input(
        id="test_biscuit_hitl",
        product_name="SuperAtta Healthy Biscuit",
        brand="TestBrand",
        claimed_category="Biscuits",
        front_claims=["100% Whole Wheat Atta", "Zero Preservatives"],
        ingredients_text="Refined Wheat Flour (Maida) 60%, Whole Wheat Flour (Atta) 20%, Sugar 22%, Palm Oil, INS 500(ii)."
    )

    thread_id = "test_audit_session_001"

    # Step 1: Start audit and verify it pauses at HITL checkpoint
    res1 = graph.start_audit(product, thread_id=thread_id)
    assert res1["status"] == "INTERRUPTED", f"Expected INTERRUPTED but got {res1['status']}"
    payload = res1["interrupt_payload"]
    
    print("[OK] Graph paused at HITL Checkpoint.")
    print(f"     Contradictions detected: {len(payload['contradictions'])}")
    print(f"     Dynamic Health Triggers: {len(payload['dynamic_health_triggers'])}")
    
    assert len(payload["contradictions"]) > 0, "Expected at least 1 marketing contradiction"
    contradiction_claim = payload["contradictions"][0]["claim"]
    assert "Atta" in contradiction_claim or "Whole Wheat" in contradiction_claim

    # Verify dynamic triggers
    trigger_keys = [t["condition_key"] for t in payload["dynamic_health_triggers"]]
    assert "diabetic" in trigger_keys, "Expected high sugar to trigger diabetic inquiry"
    assert "allergy_gluten" in trigger_keys, "Expected wheat/maida to trigger gluten allergy inquiry"
    print(f"     Trigger Keys Identified: {trigger_keys}")

    # Step 2: Human Adjudication - Dismiss the violation and set Diabetic = True
    adjudication = HITLAdjudicationPayload(
        claim_adjudications=[
            ClaimAdjudication(claim=contradiction_claim, decision="DISMISSED", human_notes="Allowed as trade puffery.")
        ],
        health_profile={"diabetic": True, "allergies": []},
        auditor_directive="CONFIRM_FINDINGS",
        expert_notes="Human Safety Officer cleared marketing puffery, flagged high sugar for diabetics."
    )

    final_report = graph.resume_audit(adjudication.model_dump(), thread_id=thread_id)
    print("[OK] Graph resumed and synthesized final report.")
    print(f"     Final Contradictions Count: {len(final_report.contradictions)}")
    print(f"     Personalized Health Alerts: {len(final_report.user_health_alerts)}")
    print(f"     Is Human Verified: {final_report.is_human_verified}")
    print(f"     Executive Summary: {final_report.executive_summary}")

    # Since the human dismissed the contradiction, it must NOT be in final_report.contradictions!
    assert len(final_report.contradictions) == 0, "Dismissed contradiction should not appear in final report"
    assert final_report.is_human_verified is True, "Report must be marked as human verified"
    assert len(final_report.user_health_alerts) > 0, "Diabetic alert should be present"
    assert "Human Safety Officer" in final_report.executive_summary

    print("=== HITL ADJUDICATION TEST PASSED 100%! ===")


if __name__ == "__main__":
    test_hitl_adjudication()

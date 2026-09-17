"""
Day 6 Automated Test Suite.
Verifies Human-in-the-Loop (HITL) state persistence using SqliteSaver,
the interrupt() primitive, and resuming graphs with personalized health profiles.
"""

import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.types import Command
from src.extractor import build_product_input
from src.hitl import NutriAuditHITLGraph, UserHealthProfile


def run_day6_tests():
    print("=================================================================")
    print("    DAY 6 TEST SUITE: HUMAN-IN-THE-LOOP (HITL) CHECKPOINTING     ")
    print("=================================================================")

    db_path = os.path.join("data", "audit_checkpoints.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    hitl_graph = NutriAuditHITLGraph(db_path=db_path)
    print(f"[INIT] NutriAuditHITLGraph initialized with SqliteSaver ({db_path})")

    dataset_path = os.path.join("data", "sample_products", "test_products.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    # -------------------------------------------------------------
    # Test 1: VitaWheat with Diabetic + Gluten Allergy Profile
    # -------------------------------------------------------------
    print("\n--- 1. Testing HITL Interrupt on VitaWheat Atta Biscuits ---")
    p1 = build_product_input(
        id=products[0]["id"],
        product_name=products[0]["product_name"],
        brand=products[0]["brand"],
        claimed_category=products[0]["claimed_category"],
        front_claims=products[0]["front_claims"],
        ingredients_text=products[0]["ingredients_text"],
        nutritional_facts=products[0].get("nutritional_facts_per_100g")
    )

    thread_config_1 = {"configurable": {"thread_id": "session_user_diabetic_celiac"}}

    initial_state_1 = {
        "product": p1,
        "decoded_additives": [],
        "disguised_sugars": [],
        "regulatory_citations": [],
        "mcp_alerts": [],
        "contradictions": [],
        "user_health_alerts": [],
        "nova_group": 0,
        "overall_verdict": "",
        "executive_summary": "",
        "reflection_count": 0,
        "quality_passed": False,
        "audit_report": None
    }

    # Step A: Run until interrupt
    print("  [EXECUTE] Running LangGraph up to HITL Checkpoint...")
    events = list(hitl_graph.app.stream(initial_state_1, config=thread_config_1))
    
    # Verify interrupt occurred
    state_snapshot = hitl_graph.app.get_state(thread_config_1)
    assert len(state_snapshot.tasks) > 0, "Execution must pause at interrupt task"
    assert len(state_snapshot.tasks[0].interrupts) > 0, "Must contain active interrupt"
    
    interrupt_payload = state_snapshot.tasks[0].interrupts[0].value
    print("  [INTERRUPT TRIGGERED] Graph safely paused execution.")
    print(f"  Payload sent to Human: {interrupt_payload['prompt']}")
    print(f"  Additives detected before pause: {interrupt_payload['detected_additives_count']}")

    # Step B: Human User inputs Medical Constraints
    print("\n  [HUMAN INPUT] User confirms medical profile: Diabetic = True, Allergies = ['Gluten']")
    user_medical_input = {
        "diabetic": True,
        "allergies": ["Gluten"],
        "is_child": False,
        "hypertensive": True
    }

    # Step C: Resume graph execution with Command(resume=...)
    print("  [RESUME] Resuming graph from SQLite checkpoint with human input...")
    resumed_events = list(hitl_graph.app.stream(Command(resume=user_medical_input), config=thread_config_1))
    
    final_state = hitl_graph.app.get_state(thread_config_1).values
    final_report = final_state["audit_report"]
    
    print(f"  [COMPLETED] Final Verdict: {final_report.overall_health_verdict}")
    print(f"  Personalized Medical Alerts ({len(final_report.user_health_alerts)}):")
    for alert in final_report.user_health_alerts:
        print(f"    [ALERT] {alert}")

    assert any("GLUTEN" in a for a in final_report.user_health_alerts), "Must include Gluten allergy alert"
    assert any("DIABETES" in a for a in final_report.user_health_alerts), "Must include Diabetes sugar alert"
    print("  [PASS] Successfully gated and personalized report via HITL!\n")

    # -------------------------------------------------------------
    # Test 2: ChocoMalt with Pediatric (Child) Profile
    # -------------------------------------------------------------
    print("--- 2. Testing HITL Interrupt on ChocoMalt for a Child ---")
    p2 = build_product_input(
        id=products[1]["id"],
        product_name=products[1]["product_name"],
        brand=products[1]["brand"],
        claimed_category=products[1]["claimed_category"],
        front_claims=products[1]["front_claims"],
        ingredients_text=products[1]["ingredients_text"],
        nutritional_facts=products[1].get("nutritional_facts_per_100g")
    )
    thread_config_2 = {"configurable": {"thread_id": "session_child_pediatric"}}
    
    # Run to interrupt
    list(hitl_graph.app.stream({**initial_state_1, "product": p2}, config=thread_config_2))
    
    # Resume with Child profile
    list(hitl_graph.app.stream(Command(resume={"is_child": True, "diabetic": False}), config=thread_config_2))
    
    final_state_2 = hitl_graph.app.get_state(thread_config_2).values
    final_report_2 = final_state_2["audit_report"]
    
    print(f"  [COMPLETED] Final Verdict: {final_report_2.overall_health_verdict}")
    for alert in final_report_2.user_health_alerts:
        print(f"    [ALERT] {alert}")
    assert any("PEDIATRIC" in a for a in final_report_2.user_health_alerts), "Must include pediatric warning"
    print("  [PASS] Pediatric safety constraints enforced via HITL!\n")

    # Verify SQLite Database file exists and has saved checkpoints
    assert os.path.exists(db_path), "SQLite database file must be created"
    assert os.path.getsize(db_path) > 0, "SQLite database must contain persisted state"
    print(f"[VERIFIED] SQLite state persistence file verified ({os.path.getsize(db_path)} bytes).")

    print("\n=================================================================")
    print("        ALL HUMAN-IN-THE-LOOP (HITL) TESTS PASSED 100%!          ")
    print("=================================================================")


if __name__ == "__main__":
    run_day6_tests()

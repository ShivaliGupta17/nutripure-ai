"""
Day 5 Automated Test Suite.
Verifies the compiled LangGraph state machine executing across benchmark products:
VitaWheat, ChocoMalt, RealBerry, and PureGrain Oats.
"""

import json
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.extractor import build_product_input
from src.graph import NutriAuditGraph
from src.schemas import AuditReport


def run_day5_tests():
    print("=================================================================")
    print("        DAY 5 TEST SUITE: LANGGRAPH CYCLIC STATE MACHINE         ")
    print("=================================================================")

    # 1. Initialize LangGraph Workflow
    print("[INIT] Initializing LangGraph Workflow...")
    graph = NutriAuditGraph()
    print("[INIT] Compiled LangGraph State Machine successfully.\n")

    # 2. Load Benchmark Products
    dataset_path = os.path.join("data", "sample_products", "test_products.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    # -------------------------------------------------------------
    # Test 1: VitaWheat Atta Digestives (Fake Atta Biscuit)
    # -------------------------------------------------------------
    print("--- 1. Executing LangGraph on VitaWheat Atta Digestives ---")
    p1 = build_product_input(
        id=products[0]["id"],
        product_name=products[0]["product_name"],
        brand=products[0]["brand"],
        claimed_category=products[0]["claimed_category"],
        front_claims=products[0]["front_claims"],
        ingredients_text=products[0]["ingredients_text"],
        nutritional_facts=products[0].get("nutritional_facts_per_100g")
    )
    report1: AuditReport = graph.run_audit(p1)
    print(f"  Verdict: {report1.overall_health_verdict}")
    print(f"  NOVA Group: {report1.nova_group} (Ultra-Processed)")
    print(f"  Deceptive Claims: {report1.deceptive_claims_count}")
    for c in report1.contradictions:
        print(f"    * [{c.severity}] Claim: '{c.claim}' -> Evidence: {c.evidence}")
    assert report1.overall_health_verdict == "UNHEALTHY / MISLEADING"
    assert report1.nova_group == 4
    assert any("Section 7" in (c.relevant_regulation or "") for c in report1.contradictions)
    print("  [PASS] VitaWheat Atta violation accurately exposed by LangGraph.\n")

    # -------------------------------------------------------------
    # Test 2: ChocoMalt Junior Health Drink (Hidden Maltodextrin)
    # -------------------------------------------------------------
    print("--- 2. Executing LangGraph on ChocoMalt Health Drink ---")
    p2 = build_product_input(
        id=products[1]["id"],
        product_name=products[1]["product_name"],
        brand=products[1]["brand"],
        claimed_category=products[1]["claimed_category"],
        front_claims=products[1]["front_claims"],
        ingredients_text=products[1]["ingredients_text"],
        nutritional_facts=products[1].get("nutritional_facts_per_100g")
    )
    report2: AuditReport = graph.run_audit(p2)
    print(f"  Verdict: {report2.overall_health_verdict}")
    print(f"  Disguised Sugars Found: {report2.disguised_sugars_found}")
    assert report2.overall_health_verdict == "UNHEALTHY / MISLEADING"
    assert "Maltodextrin" in report2.disguised_sugars_found
    print("  [PASS] ChocoMalt deceptive 'No Added Sugar' caught with Maltodextrin.\n")

    # -------------------------------------------------------------
    # Test 3: RealBerry 100% Natural Juice (Synthetic Preservative)
    # -------------------------------------------------------------
    print("--- 3. Executing LangGraph on RealBerry Fruit Delight ---")
    p3 = build_product_input(
        id=products[2]["id"],
        product_name=products[2]["product_name"],
        brand=products[2]["brand"],
        claimed_category=products[2]["claimed_category"],
        front_claims=products[2]["front_claims"],
        ingredients_text=products[2]["ingredients_text"],
        nutritional_facts=products[2].get("nutritional_facts_per_100g")
    )
    report3: AuditReport = graph.run_audit(p3)
    print(f"  Verdict: {report3.overall_health_verdict}")
    has_benzene_alert = any("Benzene" in c.evidence for c in report3.contradictions)
    assert has_benzene_alert, "Must identify Sodium Benzoate + Vitamin C Benzene hazard"
    print("  [PASS] RealBerry synthetic preservative and Benzene hazard exposed.\n")

    # -------------------------------------------------------------
    # Test 4: PureGrain Rolled Oats (Clean Control)
    # -------------------------------------------------------------
    print("--- 4. Executing LangGraph on PureGrain Rolled Oats (Control) ---")
    p4 = build_product_input(
        id=products[4]["id"],
        product_name=products[4]["product_name"],
        brand=products[4]["brand"],
        claimed_category=products[4]["claimed_category"],
        front_claims=products[4]["front_claims"],
        ingredients_text=products[4]["ingredients_text"],
        nutritional_facts=products[4].get("nutritional_facts_per_100g")
    )
    report4: AuditReport = graph.run_audit(p4)
    print(f"  Verdict: {report4.overall_health_verdict}")
    print(f"  NOVA Group: {report4.nova_group} (Minimally Processed)")
    print(f"  Deceptive Claims: {report4.deceptive_claims_count}")
    assert report4.overall_health_verdict == "CLEAN"
    assert report4.nova_group == 1
    assert report4.deceptive_claims_count == 0
    print("  [PASS] Clean product correctly classified as CLEAN with 0 false alarms.\n")

    print("=================================================================")
    print("     ALL LANGGRAPH STATE MACHINE AUDIT TESTS PASSED 100%!        ")
    print("=================================================================")


if __name__ == "__main__":
    run_day5_tests()

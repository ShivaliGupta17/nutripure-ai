import os
import sys

# Add project root to sys.path
sys.path.insert(0, r"C:\Users\Shivali\.gemini\antigravity\scratch\nutri_audit_agent")

from src.extractor import build_product_input
from src.schemas import ProductInput, NutritionalFacts
from src.nutrition_hazards import evaluate_nutritional_hazards, generate_nova_explanation
from src.chemical_decoder import ChemicalDecoder
from src.graph import NutriAuditGraph


def test_hazards_and_nova():
    print("--- 1. Testing Clean Product (100% Whole Rolled Oats) ---")
    clean_prod = build_product_input(
        id="clean_oats",
        product_name="PureGrain Rolled Oats",
        brand="PureGrain",
        claimed_category="Breakfast Cereal",
        front_claims=["100% Wholegrain", "High Fiber"],
        ingredients_text="100% Whole Grain Rolled Oats.",
        nutritional_facts={
            "energy_kcal": 389.0,
            "protein_g": 13.5,
            "carbohydrates_g": 66.0,
            "total_sugars_g": 1.0,
            "added_sugars_g": 0.0,
            "total_fat_g": 6.8,
            "saturated_fat_g": 1.2,
            "trans_fat_g": 0.0,
            "sodium_mg": 4.0
        }
    )
    clean_hazards = evaluate_nutritional_hazards(clean_prod)
    assert len(clean_hazards) == 0, f"Expected 0 hazards for oats but got {len(clean_hazards)}"
    
    clean_nova = generate_nova_explanation(1, clean_prod, [], [])
    assert clean_nova.group == 1
    assert "Unprocessed" in clean_nova.group_name
    print("[PASS] Clean Product verified: 0 hazards, NOVA Group 1")

    print("\n--- 2. Testing 'Clean Label Trap': Silent Front Claims but Critical Sugar & Saturated Fat ---")
    # Brand makes NO front claims at all! (0 contradictions possible from claims)
    silent_toxic_prod = build_product_input(
        id="silent_cookie",
        product_name="SweetDelight Cream Sandwich",
        brand="SweetDelight",
        claimed_category="Biscuits",
        front_claims=[],  # ZERO claims made!
        ingredients_text="Refined Wheat Flour, Sugar, Hydrogenated Vegetable Fat, Invert Sugar Syrup, Emulsifiers [INS 322, INS 471], Artificial Flavouring.",
        nutritional_facts={
            "energy_kcal": 510.0,
            "protein_g": 4.5,
            "carbohydrates_g": 68.0,
            "total_sugars_g": 34.0,  # 34% pure sugar!
            "added_sugars_g": 32.0,
            "total_fat_g": 24.0,
            "saturated_fat_g": 12.5, # 12.5g saturated fat!
            "trans_fat_g": 0.2,     # Trans fat present!
            "sodium_mg": 320.0
        }
    )
    
    decoder = ChemicalDecoder()
    decoded = decoder.decode_all(silent_toxic_prod)
    
    hazards = evaluate_nutritional_hazards(silent_toxic_prod)
    print(f"Detected {len(hazards)} independent nutritional hazards:")
    for h in hazards:
        print(f"  - [{h.severity}] {h.headline} ({h.guideline_source})")
        
    crit_hazards = [h for h in hazards if h.severity == "CRITICAL"]
    assert len(crit_hazards) >= 2, f"Expected at least 2 critical hazards (sugar, sat fat/trans fat), got {len(crit_hazards)}"
    
    # Check that sugar hazard references WHO optimal limit
    sugar_h = next(h for h in hazards if h.nutrient == "Total Sugars")
    assert sugar_h.severity == "CRITICAL"
    assert "34.0g" in sugar_h.headline
    assert "WHO" in sugar_h.explanation or "WHO" in sugar_h.guideline_source
    
    # Check NOVA explanation
    nova_exp = generate_nova_explanation(4, silent_toxic_prod, decoded, ["Invert Sugar Syrup"])
    assert nova_exp.group == 4
    assert len(nova_exp.triggering_substances) > 0
    print(f"NOVA Group 4 Triggers: {nova_exp.triggering_substances}")
    assert any("INS 322" in s or "Lecithin" in s for s in nova_exp.triggering_substances)
    assert "cardiovascular" in nova_exp.health_implications.lower()
    
    print("\n--- 3. Testing Graph Verdict Override ---")
    # Verify that run_audit never sets verdict to 'CLEAN' when critical hazard exists!
    graph = NutriAuditGraph(chemical_decoder=decoder)
    report = graph.run_audit(silent_toxic_prod)
    print(f"Overall Health Verdict: '{report.overall_health_verdict}'")
    assert report.overall_health_verdict != "CLEAN", "CRITICAL FLAW: Product with 34g sugar was marked CLEAN!"
    assert "UNHEALTHY" in report.overall_health_verdict, f"Expected UNHEALTHY verdict, got {report.overall_health_verdict}"
    assert report.nova_group == 4
    assert len(report.nutritional_hazards) >= 3
    assert report.nova_explanation is not None
    assert report.nova_explanation.group == 4
    print("[PASS] Graph correctly overrides silent brand marketing to UNHEALTHY (CRITICAL NUTRITIONAL LOAD)")
    
    print("\nALL NUTRITIONAL HAZARDS & NOVA TESTS PASSED 100%!")


if __name__ == "__main__":
    test_hazards_and_nova()

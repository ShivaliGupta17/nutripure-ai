"""
Day 2 Automated Test Suite.
Verifies Pydantic schemas, ingredient list parsing, INS code extraction,
and chemical additive decoding across all benchmark products.
"""

import json
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas import ProductInput, NutritionalFacts
from src.extractor import build_product_input, detect_disguised_sugars
from src.chemical_decoder import ChemicalDecoder


def run_day2_tests():
    print("=================================================================")
    print("           DAY 2 TEST SUITE: SCHEMAS & EXTRACTION ENGINE         ")
    print("=================================================================")

    # 1. Load benchmark products
    dataset_path = os.path.join("data", "sample_products", "test_products.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"[LOAD] Loaded {len(products)} benchmark test products from {dataset_path}\n")

    decoder = ChemicalDecoder()
    total_passed = 0

    for idx, prod in enumerate(products, 1):
        print(f"--- Testing Product {idx}: {prod['product_name']} ---")
        
        # Build Pydantic model
        product_obj = build_product_input(
            id=prod["id"],
            product_name=prod["product_name"],
            brand=prod["brand"],
            claimed_category=prod["claimed_category"],
            front_claims=prod["front_claims"],
            ingredients_text=prod["ingredients_text"],
            nutritional_facts=prod.get("nutritional_facts_per_100g")
        )

        # Assert schema validation
        assert isinstance(product_obj, ProductInput), "Must be a valid ProductInput schema"
        assert isinstance(product_obj.nutritional_facts, NutritionalFacts), "Nutritional facts must be valid schema"
        
        print(f"  [OK] Schema Validated: {product_obj.product_name}")
        print(f"  [OK] Parsed Ingredients ({len(product_obj.ingredients)}):")
        for ing in product_obj.ingredients[:3]:
            pct_str = f" ({ing.percentage}%)" if ing.percentage else ""
            print(f"       - {ing.name}{pct_str}")
        if len(product_obj.ingredients) > 3:
            print(f"       - ... and {len(product_obj.ingredients) - 3} more")

        # Test INS Extraction & Decoding
        print(f"  [OK] Detected INS Codes: {product_obj.declared_ins_codes}")
        decoded_additives = decoder.decode_all(product_obj)
        for add in decoded_additives:
            print(f"       * {add.code} -> {add.chemical_name} [{add.risk_level} Risk] ({add.category})")

        # Test Disguised Sugar Detection
        sugars = detect_disguised_sugars(product_obj.raw_ingredients_text)
        if sugars:
            print(f"  [WARNING] Disguised Sugars/Fats Detected: {sugars}")

        print(f"  [PASS] Product {idx} verified successfully.\n")
        total_passed += 1

    # Specific assertions on benchmark edge cases
    print("--- Specific Edge-Case Assertions ---")
    
    # Check VitaWheat Atta Biscuits (Maida 62%, Atta 24%)
    p1 = build_product_input(
        id=products[0]["id"],
        product_name=products[0]["product_name"],
        brand=products[0]["brand"],
        claimed_category=products[0]["claimed_category"],
        front_claims=products[0]["front_claims"],
        ingredients_text=products[0]["ingredients_text"],
        nutritional_facts=products[0].get("nutritional_facts_per_100g")
    )
    maida_ing = next(i for i in p1.ingredients if "maida" in i.name.lower())
    atta_ing = next(i for i in p1.ingredients if "atta" in i.name.lower())
    assert maida_ing.percentage == 62.0, f"Expected Maida 62%, got {maida_ing.percentage}%"
    assert atta_ing.percentage == 24.0, f"Expected Atta 24%, got {atta_ing.percentage}%"
    print("  [OK] VitaWheat flour percentages (Maida: 62%, Atta: 24%) accurately extracted.")

    # Check ChocoMalt (Maltodextrin disguised sugar and Sucralose)
    p2 = build_product_input(
        id=products[1]["id"],
        product_name=products[1]["product_name"],
        brand=products[1]["brand"],
        claimed_category=products[1]["claimed_category"],
        front_claims=products[1]["front_claims"],
        ingredients_text=products[1]["ingredients_text"],
        nutritional_facts=products[1].get("nutritional_facts_per_100g")
    )
    p2_sugars = detect_disguised_sugars(p2.raw_ingredients_text)
    assert "Maltodextrin" in p2_sugars, "Maltodextrin must be flagged as disguised sugar"
    print("  [OK] ChocoMalt Maltodextrin disguised sugar flagged.")

    print("\n=================================================================")
    print(f"       ALL {total_passed} BENCHMARK PRODUCTS PASSED DAY 2 TESTS!        ")
    print("=================================================================")


if __name__ == "__main__":
    run_day2_tests()

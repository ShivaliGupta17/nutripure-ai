"""
Day 3 Automated Test Suite.
Verifies ChromaDB vector database index building, chunking of official
FSSAI 32-page Gazette PDF + Markdown documents, and semantic compliance queries.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.rag_engine import RegulatoryRAG


def run_day3_tests():
    print("=================================================================")
    print("           DAY 3 TEST SUITE: REGULATORY RAG ENGINE               ")
    print("=================================================================")

    # 1. Initialize RAG Engine
    persist_dir = os.path.join("data", "chroma_db")
    rag = RegulatoryRAG(persist_dir=persist_dir)
    print("[INIT] Initialized RegulatoryRAG with ChromaDB persistent storage.")

    # 2. Build / Ingest Index
    print("\n--- Ingesting Documents (Official FSSAI 32-Page PDF + Markdown Guidelines) ---")
    indexed_count = rag.build_index(force_reload=True)
    print(f"[INDEX] Successfully indexed {indexed_count} regulatory chunks into ChromaDB.")
    assert indexed_count > 0, "ChromaDB index must contain chunks"

    # 3. Test Query 1: Atta / Whole Wheat Claims
    print("\n--- Test Query 1: Atta / Whole Wheat Claim Legality ---")
    query1 = "What are the legal conditions for claiming 100% Atta or Whole Wheat Biscuits?"
    results1 = rag.query(query1, n_results=2)
    for idx, r in enumerate(results1, 1):
        print(f"  Result {idx} [Citation: {r['citation']}]:")
        print(f"  Snippet: {r['text'][:200]}...\n")
    assert any("whole wheat" in r["text"].lower() or "atta" in r["text"].lower() for r in results1), \
        "Query 1 must return Whole Wheat / Atta legal standards"
    print("  [PASS] Query 1 successfully retrieved Atta / Whole Wheat regulations.")

    # 4. Test Query 2: Sugar-Free / No Added Sugar with Maltodextrin
    print("--- Test Query 2: 'No Added Sugar' Claim with Maltodextrin ---")
    query2 = "Is it legal to claim No Added Sugar when Maltodextrin is used?"
    results2 = rag.query(query2, n_results=2)
    for idx, r in enumerate(results2, 1):
        print(f"  Result {idx} [Citation: {r['citation']}]:")
        print(f"  Snippet: {r['text'][:200]}...\n")
    assert any("sugar" in r["text"].lower() for r in results2), \
        "Query 2 must return Sugar / Sweetener regulations"
    print("  [PASS] Query 2 successfully retrieved Sugar claims standards.")

    # 5. Test Query 3: Sodium Benzoate + Vitamin C Benzene Hazard
    print("--- Test Query 3: Sodium Benzoate (INS 211) & Vitamin C Chemical Hazard ---")
    query3 = "What is the hazard of combining Sodium Benzoate with Vitamin C Ascorbic Acid?"
    results3 = rag.query(query3, n_results=2)
    for idx, r in enumerate(results3, 1):
        print(f"  Result {idx} [Citation: {r['citation']}]:")
        print(f"  Snippet: {r['text'][:200]}...\n")
    assert any("benzoate" in r["text"].lower() or "benzene" in r["text"].lower() for r in results3), \
        "Query 3 must return Benzoate chemical interaction hazard"
    print("  [PASS] Query 3 successfully retrieved Sodium Benzoate chemical risk standards.")

    # 6. Test Targeted Marketing Claim Verification Method
    print("--- Test 4: Targeted Verification for VitaWheat Atta Claim ---")
    audit = rag.verify_marketing_claim(
        claim="100% Whole Wheat Atta",
        ingredient_details="Refined Wheat Flour (Maida) 62%, Whole Wheat Flour (Atta) 24%"
    )
    print(f"  Claim Under Audit: '{audit['claim']}'")
    print(f"  Retrieved Citations: {audit['citations']}")
    assert len(audit["relevant_clauses"]) > 0, "Must return at least one relevant clause"
    print("  [PASS] Targeted claim verification pipeline functioning.")

    print("\n=================================================================")
    print("         ALL REGULATORY RAG TESTS PASSED SUCCESSFULLY!           ")
    print("=================================================================")


if __name__ == "__main__":
    run_day3_tests()

"""
Day 4 Automated Test Suite.
Verifies Model Context Protocol (MCP) standardized tool discovery,
input schema compliance, and live tool execution routing.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp_tools import MCPToolRegistry


def run_day4_tests():
    print("=================================================================")
    print("           DAY 4 TEST SUITE: MODEL CONTEXT PROTOCOL (MCP)        ")
    print("=================================================================")

    registry = MCPToolRegistry()
    
    # 1. Test MCP Tool Discovery
    print("--- 1. Testing Standardized MCP Tool Discovery ---")
    tools = registry.list_tools()
    print(f"[DISCOVERY] Registered {len(tools)} MCP Tools:")
    for t in tools:
        print(f"  * Tool Name: '{t['name']}'")
        print(f"    Description: {t['description'][:80]}...")
        print(f"    Required Args: {t['inputSchema']['required']}")
        assert "name" in t and "description" in t and "inputSchema" in t, \
            "Must adhere to MCP tool schema format"
    print("  [PASS] MCP Tool Catalog compliant with Model Context Protocol standard.\n")

    # 2. Test Chemical Toxicity MCP Tool
    print("--- 2. Testing Chemical Toxicity MCP Tool ---")
    
    # Case A: Banned Titanium Dioxide (INS 171)
    res_banned = registry.call_tool("query_chemical_toxicity", {"chemical_or_ins": "INS 171"})
    print("  Query: 'INS 171' (Titanium Dioxide)")
    print(f"  Result: {res_banned['chemical_name']} | CAS: {res_banned['cas_number']}")
    print(f"  Status: {res_banned['international_status']}")
    print(f"  Toxicity: {res_banned['toxicity_profile']}")
    assert res_banned["status"] == "SUCCESS"
    assert "BANNED" in res_banned["international_status"]
    print("  [PASS] Successfully retrieved international ban data for INS 171.\n")

    # Case B: Allergenic Tartrazine (INS 102)
    res_allergen = registry.call_tool("query_chemical_toxicity", {"chemical_or_ins": "INS 102"})
    print("  Query: 'INS 102' (Tartrazine)")
    print(f"  Result: {res_allergen['chemical_name']} | Advisory: {res_allergen['advisory']}")
    assert "histamine" in res_allergen["advisory"].lower() or "asthmatic" in res_allergen["advisory"].lower()
    print("  [PASS] Successfully retrieved allergenic warnings for INS 102.\n")

    # 3. Test FSSAI Live Product Alerts MCP Tool
    print("--- 3. Testing FSSAI Live Regulatory Alerts MCP Tool ---")
    
    # Case A: Bournvita / Malt Drinks "Health Drink" Crackdown
    res_alert = registry.call_tool("check_fssai_product_alerts", {
        "product_or_brand": "Bournvita",
        "claim_type": "Health Drink"
    })
    print(f"  Query: 'Bournvita' (Claim: 'Health Drink') -> Found {res_alert['alerts_count']} alerts")
    for alert in res_alert["alerts"]:
        print(f"  * [{alert['advisory_id']}] {alert['title']}")
        print(f"    Action: {alert['enforcement_action'][:120]}...")
    assert res_alert["alerts_count"] > 0
    assert "ORDERED REMOVAL" in res_alert["alerts"][0]["enforcement_action"]
    print("  [PASS] Successfully retrieved live FSSAI directive on 'Health Drink' misleading claims.\n")

    # Case B: Atta / Whole Wheat Biscuits Enforcement
    res_atta = registry.call_tool("check_fssai_product_alerts", {
        "product_or_brand": "Digestive Biscuits",
        "claim_type": "Whole Wheat"
    })
    print(f"  Query: 'Digestive Biscuits' (Claim: 'Whole Wheat') -> Found {res_atta['alerts_count']} alerts")
    assert res_atta["alerts_count"] > 0
    print(f"  * Enforcement: {res_atta['alerts'][0]['enforcement_action'][:100]}...")
    print("  [PASS] Successfully retrieved FSSAI 60% whole wheat minimum threshold directive.\n")

    print("=================================================================")
    print("         ALL MODEL CONTEXT PROTOCOL (MCP) TESTS PASSED!          ")
    print("=================================================================")


if __name__ == "__main__":
    run_day4_tests()

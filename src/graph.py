"""
LangGraph State Machine for NutriPure AI.
Coordinates multi-node agentic reasoning: chemical decoding,
regulatory RAG lookup, claim contradiction detection, NOVA scoring, and reflection.
"""

import os
import json
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

load_dotenv()

from src.schemas import ProductInput, DecodedAdditive, ContradictionItem, AuditReport
from src.chemical_decoder import ChemicalDecoder
from src.extractor import detect_disguised_sugars
from src.rag_engine import RegulatoryRAG
from src.mcp_tools import MCPToolRegistry
from src.nutrition_hazards import evaluate_nutritional_hazards, generate_nova_explanation


class AgentState(TypedDict):
    """Shared state dictionary passed across LangGraph nodes."""
    product: ProductInput
    decoded_additives: List[DecodedAdditive]
    disguised_sugars: List[str]
    regulatory_citations: List[str]
    mcp_alerts: List[Dict[str, Any]]
    contradictions: List[ContradictionItem]
    nova_group: int
    overall_verdict: str
    executive_summary: str
    user_health_alerts: List[str]
    reflection_count: int
    quality_passed: bool
    audit_report: Optional[AuditReport]
    hitl_payload: Optional[Any]
    is_human_verified: Optional[bool]

def evaluate_marketing_claims_deterministic(
    product: ProductInput,
    decoded: List[DecodedAdditive],
    disguised: List[str]
) -> List[ContradictionItem]:
    """
    Authoritative contradiction evaluator comparing front claims with ingredients and nutrition:
    A. Atta / Whole Wheat Contradiction Check
    B. Sugar-Free / No Added Sugar Contradiction Check
    C. 100% Natural & No Preservatives Contradiction Check
    D. Chemical Interaction Hazard (Sodium Benzoate + Vitamin C)
    E. Premium Oil / Blended Fat Deception (Surrogate Fat Emphasis)
    F. Deceptive Comparative Health Claims (Healthier / Healthy / Guilt-Free)
    G. Himalayan / Rock Salt Sodium Risk Illusion
    """
    contradictions = []
    lower_claims = " ".join(product.front_claims).lower()
    lower_ingredients = product.raw_ingredients_text.lower()
    nf = getattr(product, "nutritional_facts", None)
    
    # A. Atta / Whole Wheat Contradiction Check
    if "whole wheat" in lower_claims or "atta" in lower_claims:
        maida_pct = 0.0
        atta_pct = 0.0
        has_maida = False
        for ing in product.ingredients:
            if "maida" in ing.name.lower() or "refined wheat flour" in ing.name.lower():
                has_maida = True
                if ing.percentage:
                    maida_pct = ing.percentage
            if "atta" in ing.name.lower() or "whole wheat" in ing.name.lower():
                if ing.percentage:
                    atta_pct = ing.percentage
                    
        if maida_pct > atta_pct or (atta_pct > 0 and atta_pct < 60.0):
            contradictions.append(ContradictionItem(
                claim="100% Whole Wheat Atta",
                contradiction_type="LEGAL_VIOLATION",
                evidence=f"Refined Wheat Flour (Maida) comprises {maida_pct}% of total product while Atta is only {atta_pct}%.",
                severity="HIGH",
                relevant_regulation="FSSAI Advertising and Claims Regulation 2020, Section 7 (Minimum 60% Whole Wheat rule)."
            ))
        elif "100%" in lower_claims and has_maida and ("whole wheat" in lower_claims or "atta" in lower_claims):
            contradictions.append(ContradictionItem(
                claim="100% Whole Wheat Atta",
                contradiction_type="LEGAL_VIOLATION",
                evidence="Packaging advertises '100% Whole Wheat / Atta', but ingredients list contains Refined Wheat Flour (Maida).",
                severity="HIGH",
                relevant_regulation="FSSAI Advertising and Claims Regulation 2020, Regulation 4(1)."
            ))

    # B. Sugar-Free / No Added Sugar Contradiction Check
    if "no added sugar" in lower_claims or "zero sugar" in lower_claims or "sugar free" in lower_claims:
        if "maltodextrin" in [s.lower() for s in disguised]:
            contradictions.append(ContradictionItem(
                claim="No Added Sugar",
                contradiction_type="DECEPTIVE_MARKETING",
                evidence="Contains high-glycemic Maltodextrin (GI 110-185, spikes blood glucose faster than table sugar).",
                severity="HIGH",
                relevant_regulation="FSSAI Schedule II, Section 4 (Maltodextrin bulking prohibition for No Added Sugar claims)."
            ))
        if any(add.is_disguised_sugar for add in decoded):
            contradictions.append(ContradictionItem(
                claim="Zero Sugar",
                contradiction_type="MISLEADING",
                evidence="Substituted table sugar with artificial non-sugar sweeteners (WHO 2023 NSS advisory).",
                severity="MEDIUM",
                relevant_regulation="WHO 2023 Guideline on Non-Sugar Sweeteners."
            ))
        if nf and nf.total_sugars_g is not None and nf.total_sugars_g > 0.5:
            contradictions.append(ContradictionItem(
                claim="Zero Sugar / Sugar Free",
                contradiction_type="LEGAL_VIOLATION",
                evidence=f"Front pack claims 'Zero Sugar', but nutrition table declares {nf.total_sugars_g}g sugars per 100g (legal threshold is <= 0.5g per 100g).",
                severity="HIGH",
                relevant_regulation="FSSAI Advertising and Claims Regulations 2020, Schedule I (Sugar Free Conditions)."
            ))

    # C. 100% Natural & No Preservatives Contradiction Check
    if "natural" in lower_claims or "no preservative" in lower_claims:
        synthetic_additives = [
            add for add in decoded 
            if add.category in ["Preservative", "Food Coloring", "Synthetic Food Color", "Artificial Sweetener"]
        ]
        if synthetic_additives:
            names = ", ".join([f"{a.chemical_name} ({a.code})" for a in synthetic_additives])
            contradictions.append(ContradictionItem(
                claim="100% Natural / No Preservatives",
                contradiction_type="LEGAL_VIOLATION",
                evidence=f"Product contains synthetic chemical additives: {names}.",
                severity="HIGH",
                relevant_regulation="FSSAI General Principles, Regulation 4 (Prohibits 'Natural' claim when chemical additives are present)."
            ))

    # D. Chemical Interaction Hazard (Sodium Benzoate + Vitamin C)
    has_benzoate = any("211" in a.code for a in decoded)
    has_vit_c = "vitamin c" in lower_ingredients or "ascorbic acid" in lower_ingredients or any("300" in a.code for a in decoded)
    if has_benzoate and has_vit_c:
        contradictions.append(ContradictionItem(
            claim="Clean / Healthy Beverage",
            contradiction_type="HEALTH_HAZARD",
            evidence="Contains combination of Sodium Benzoate (INS 211) and Vitamin C (INS 300) which can react to form Benzene (carcinogen).",
            severity="HIGH",
            relevant_regulation="WHO Food Additives Safety Alert (Benzene formation in acidic beverages)."
        ))

    # E. Premium Oil / Blended Fat Deception
    premium_oils = ['groundnut', 'olive', 'desi ghee', 'ghee', 'mustard', 'coconut oil', 'sesame', 'avocado', 'sunflower', 'canola']
    cheap_fats = ['partially hydrogenated', 'hydrogenated', 'vanaspati', 'palm oil', 'palmolein', 'refined palm', 'fractionated vegetable oil']

    for claim in product.front_claims:
        c_low = claim.lower()
        found_prem = next((p for p in premium_oils if p in c_low), None)
        if found_prem:
            found_cheap = [cf for cf in cheap_fats if cf in lower_ingredients]
            if found_cheap:
                is_hydrogenated = any("hydrogenated" in cf or "vanaspati" in cf for cf in found_cheap)
                c_type = "LEGAL_VIOLATION" if is_hydrogenated else "DECEPTIVE_MARKETING"
                contradictions.append(ContradictionItem(
                    claim=claim,
                    contradiction_type=c_type,
                    evidence=f"Packaging prominently advertises '{claim}', but the ingredient list reveals cheap {found_cheap[0].title()} is used as a primary or blended fat before or alongside {found_prem.title()} oil.",
                    severity="HIGH",
                    relevant_regulation="FSSAI Advertising and Claims Regulations 2020, Regulation 4(1) & Regulation 7 (Surrogate Fat Emphasis & Misleading Quality Claims)."
                ))

    # F. Deceptive Comparative Health Claims ('HEALTHIER', 'HEALTHY', 'GUILT FREE')
    health_keywords = ['healthier', 'healthy', 'guilt free', 'guilt-free', 'fit', 'wholesome', 'smart choice', 'good for health', 'wellness']
    for claim in product.front_claims:
        c_low = claim.lower()
        if any(hk in c_low for hk in health_keywords):
            reasons = []
            if nf and nf.trans_fat_g is not None and nf.trans_fat_g > 0.0:
                reasons.append(f"dangerous Trans Fat ({nf.trans_fat_g:.2f}g per 100g)")
            if nf and nf.saturated_fat_g is not None and nf.saturated_fat_g > 5.0:
                reasons.append(f"high Saturated Fat ({nf.saturated_fat_g:.1f}g per 100g)")
            if nf and nf.sodium_mg is not None and nf.sodium_mg > 600.0:
                reasons.append(f"high Sodium ({nf.sodium_mg:.0f}mg per 100g)")
            if nf and nf.total_sugars_g is not None and nf.total_sugars_g > 15.0:
                reasons.append(f"high Sugar ({nf.total_sugars_g:.1f}g per 100g)")
                
            if reasons:
                reasons_str = " and ".join(reasons)
                contradictions.append(ContradictionItem(
                    claim=claim,
                    contradiction_type="LEGAL_VIOLATION",
                    evidence=f"Pack claims '{claim}', but product formulation contains {reasons_str}. Statutory comparative health claims prohibit 'healthier' claims on foods high in saturated or trans fats.",
                    severity="HIGH",
                    relevant_regulation="FSSAI Advertising and Claims Regulations 2020, Regulation 7(1) (Comparative Health Claim Thresholds) & WHO REPLACE Guidelines."
                ))

    # G. Himalayan / Rock Salt Mineral Illusion
    salt_keywords = ['rock salt', 'pink salt', 'himalayan rock salt', 'himalayan salt', 'sendha namak']
    for claim in product.front_claims:
        c_low = claim.lower()
        if any(sk in c_low for sk in salt_keywords):
            if nf and nf.sodium_mg is not None and nf.sodium_mg > 300.0:
                contradictions.append(ContradictionItem(
                    claim=claim,
                    contradiction_type="MISLEADING",
                    evidence=f"Front pack highlights '{claim}' as a premium health attribute. However, Rock/Pink Salt consists of 98%+ Sodium Chloride (delivering {nf.sodium_mg:.0f}mg sodium/100g) and carries standard cardiovascular risks of high sodium intake.",
                    severity="MEDIUM",
                    relevant_regulation="FSSAI Schedule II & ICMR-NIN 2024 Dietary Guidelines (Sodium Risk Advisory)."
                ))

    return contradictions


def evaluate_claims_with_llm(
    product: ProductInput,
    decoded: List[DecodedAdditive],
    disguised: List[str],
    regulatory_citations: Optional[List[str]] = None
) -> Optional[List[ContradictionItem]]:
    """
    Zero-Shot LLM-as-a-Judge Claim Auditor.
    Uses LLM reasoning against general statutory food principles, ingredients, and nutrition facts.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or not product.front_claims:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        nf_dict = {}
        if getattr(product, "nutritional_facts", None):
            nf = product.nutritional_facts
            for field in ["energy_kcal", "protein_g", "carbohydrates_g", "total_sugars_g", "added_sugars_g", "total_fat_g", "saturated_fat_g", "trans_fat_g", "sodium_mg"]:
                val = getattr(nf, field, None)
                if val is not None:
                    nf_dict[field] = val

        decoded_summary = [f"{a.chemical_name} ({a.code}) - {a.category}" for a in decoded]
        
        prompt = f"""
You are an expert FSSAI regulatory compliance judge and food safety auditor for NutriPure AI.

Evaluate EVERY front-of-pack marketing claim against the verified ingredients declaration, additives, and nutritional declaration.

PRODUCT DETAILS:
- Brand & Name: {product.brand} - {product.product_name}
- Claimed Category: {product.claimed_category}
- Front Marketing Claims: {json.dumps(product.front_claims)}
- Ingredients List (declared in descending order of incoming weight): "{product.raw_ingredients_text}"
- Detected Additives / E-Numbers: {json.dumps(decoded_summary)}
- Disguised Sugars Identified: {json.dumps(disguised)}
- Nutritional Facts Declaration (per 100g): {json.dumps(nf_dict)}

CORE STATUTORY AUDIT PRINCIPLES:
1. ORDER OF PREDOMINANCE (FSSAI Labeling & Display 2020, Reg 5): Ingredients must be declared in descending order of incoming weight. Highlighting an ingredient on the front (e.g. 'Made with X') when an inferior fat/filler or hydrogenated vegetable oil is declared before or alongside it is deceptive surrogate marketing.
2. COMPARATIVE HEALTH CLAIMS (FSSAI Advertising 2020, Reg 7): Comparative claims like 'Healthier', 'Light', 'Fit', or 'Wholesome' are prohibited on products containing industrial trans fat (> 0g) or high saturated fat (> 5g/100g) or high sugars (> 15g/100g).
3. INGREDIENT & PURITY ILLUSIONS: Touting whole grains ('100% Atta') when refined flour (Maida) is present, claiming 'No Added Sugar' while using high-glycemic Maltodextrin or syrups, or claiming '100% Natural / No Preservatives' while using synthetic chemical additives (INS codes).
4. SODIUM / MINERAL ILLUSIONS: Marketing Rock Salt / Pink Salt as healthy when total sodium is elevated (> 300mg/100g).

TASK:
For each front claim, determine if it is COMPLIANT or CONTRADICTED/DECEPTIVE.
Return ONLY valid JSON matching this schema:
{{
  "contradictions": [
    {{
      "claim": "Exact claim string from front_claims",
      "contradiction_type": "LEGAL_VIOLATION or DECEPTIVE_MARKETING or HEALTH_HAZARD or MISLEADING",
      "evidence": "Factual evidence citing specific ingredients or nutrition figures",
      "severity": "HIGH or MEDIUM or LOW",
      "relevant_regulation": "Specific FSSAI, WHO, or ICMR-NIN citation"
    }}
  ]
}}

If a claim is truthful and compliant, omit it from contradictions. Return ONLY JSON.
"""
        resp = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a professional food law compliance auditor. You output strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=600
        )
        
        data = json.loads(resp.choices[0].message.content)
        raw_list = data.get("contradictions", [])
        items = []
        for item in raw_list:
            claim_str = item.get("claim", "")
            c_type = item.get("contradiction_type", "MISLEADING")
            if c_type not in ["LEGAL_VIOLATION", "DECEPTIVE_MARKETING", "HEALTH_HAZARD", "MISLEADING"]:
                c_type = "DECEPTIVE_MARKETING"
            sev = item.get("severity", "HIGH")
            if sev not in ["HIGH", "MEDIUM", "LOW"]:
                sev = "HIGH"
                
            items.append(ContradictionItem(
                claim=claim_str,
                contradiction_type=c_type,
                evidence=item.get("evidence", "Contradicts ingredient facts."),
                severity=sev,
                relevant_regulation=item.get("relevant_regulation", "FSSAI Regulations 2020")
            ))
        return items
    except Exception as e:
        print(f"[WARN] LLM Claim Auditor call failed: {e}. Falling back to deterministic rules.")
        return None


def evaluate_marketing_claims(
    product: ProductInput,
    decoded: List[DecodedAdditive],
    disguised: List[str],
    regulatory_citations: Optional[List[str]] = None
) -> List[ContradictionItem]:
    """
    Dual-Mode General Claim Auditor:
    1. Runs Zero-Shot LLM-as-a-Judge for general reasoning across any packaged food.
    2. Seamlessly falls back to deterministic statutory rule engine if offline or on rate limit.
    """
    llm_results = evaluate_claims_with_llm(product, decoded, disguised, regulatory_citations)
    if llm_results is not None:
        return llm_results
    return evaluate_marketing_claims_deterministic(product, decoded, disguised)


class NutriAuditGraph:
    """The core LangGraph workflow orchestrator."""

    def __init__(
        self,
        rag_engine: Optional[RegulatoryRAG] = None,
        chemical_decoder: Optional[ChemicalDecoder] = None,
        mcp_registry: Optional[MCPToolRegistry] = None
    ):
        self.rag = rag_engine or RegulatoryRAG()
        self.decoder = chemical_decoder or ChemicalDecoder()
        self.mcp = mcp_registry or MCPToolRegistry()
        self.workflow = self._build_graph()

    # ---------------------------------------------------------
    # Node 1: Decode Chemicals & Disguised Sugars
    # ---------------------------------------------------------
    def node_decode_chemicals(self, state: AgentState) -> Dict[str, Any]:
        """Resolves all INS numbers and scans for disguised industrial sugars."""
        product = state["product"]
        
        # 1. Local chemical registry decoding
        decoded = self.decoder.decode_all(product)
        
        # 2. Query MCP Chemical Registry for any high-risk or rare additives
        for item in decoded:
            if item.risk_level in ["Moderate", "High"] or "Food Additive" in item.chemical_name:
                mcp_resp = self.mcp.call_tool("query_chemical_toxicity", {"chemical_or_ins": item.code})
                if mcp_resp.get("found"):
                    if mcp_resp.get("advisory") and mcp_resp["advisory"] not in item.health_warnings:
                        item.health_warnings.append(mcp_resp["advisory"])

        # 3. Disguised sugar detection
        disguised = detect_disguised_sugars(product.raw_ingredients_text)
        
        return {
            "decoded_additives": decoded,
            "disguised_sugars": disguised
        }

    # ---------------------------------------------------------
    # Node 2: Regulatory RAG & MCP Live Search
    # ---------------------------------------------------------
    def node_regulatory_rag(self, state: AgentState) -> Dict[str, Any]:
        """Queries ChromaDB vector database and live FSSAI MCP alerts."""
        product = state["product"]
        citations = []
        
        # Query RAG for each front marketing claim
        for claim in product.front_claims:
            verification = self.rag.verify_marketing_claim(
                claim=claim,
                ingredient_details=product.raw_ingredients_text
            )
            for c in verification["citations"]:
                if c not in citations:
                    citations.append(c)

        # Query MCP for live FSSAI product recalls or category crackdowns
        mcp_res = self.mcp.call_tool("check_fssai_product_alerts", {
            "product_or_brand": f"{product.brand} {product.claimed_category}",
            "claim_type": " ".join(product.front_claims)
        })
        
        alerts = mcp_res.get("alerts", [])
        
        return {
            "regulatory_citations": citations,
            "mcp_alerts": alerts
        }

    # ---------------------------------------------------------
    # Node 3: Claim Contradiction Grader
    # ---------------------------------------------------------
    def node_claim_contradiction_grader(self, state: AgentState) -> Dict[str, Any]:
        """Exposes contradictions between front marketing claims and back ingredients."""
        product = state["product"]
        decoded = state["decoded_additives"]
        disguised = state["disguised_sugars"]
        citations = state.get("regulatory_citations", [])
        contradictions = evaluate_marketing_claims(product, decoded, disguised, citations)
        return {"contradictions": contradictions}

    # ---------------------------------------------------------
    # Node 4: Toxicity & NOVA Group Scorer
    # ---------------------------------------------------------
    def node_toxicity_and_nova_scorer(self, state: AgentState) -> Dict[str, Any]:
        """Calculates ultra-processed NOVA food classification (1 to 4)."""
        product = state["product"]
        decoded = state["decoded_additives"]
        disguised = state["disguised_sugars"]
        
        # NOVA Classification Logic:
        # Group 1: Single whole foods (e.g. 100% Oats)
        # Group 4: Ultra-processed (>= 5 ingredients, industrial additives, synthetic colors/sweeteners)
        num_ingredients = len(product.ingredients)
        num_additives = len(decoded)
        has_cosmetic_additives = any(
            a.category in ["Synthetic Food Color", "Artificial Sweetener", "Flavor Enhancer"] 
            for a in decoded
        )
        
        if num_ingredients <= 2 and num_additives == 0 and len(disguised) == 0:
            nova = 1  # Unprocessed / Minimally processed
        elif num_additives == 0 and len(disguised) == 0:
            nova = 3  # Processed
        else:
            nova = 4  # Ultra-Processed Food (UPF)
            
        return {
            "nova_group": nova,
            "quality_passed": True
        }

    # ---------------------------------------------------------
    # Conditional Edge: Self-Reflection / Quality Gate
    # ---------------------------------------------------------
    def should_reflect(self, state: AgentState) -> str:
        """Determines whether to loop back for deeper RAG retrieval or synthesize report."""
        # If no citations were retrieved but contradictions exist, loop back once
        if len(state.get("contradictions", [])) > 0 and len(state.get("regulatory_citations", [])) == 0:
            if state.get("reflection_count", 0) < 1:
                return "reflect_rag"
        return "synthesize"

    # ---------------------------------------------------------
    # Node 5: Synthesize Final Audit Report
    # ---------------------------------------------------------
    def node_synthesize_report(self, state: AgentState) -> Dict[str, Any]:
        """Compiles the final plain-English consumer audit report."""
        product = state["product"]
        contradictions = state["contradictions"]
        decoded = state["decoded_additives"]
        disguised = state["disguised_sugars"]
        nova = state["nova_group"]
        
        # Evaluate independent WHO/ICMR-NIN nutritional hazards
        hazards = evaluate_nutritional_hazards(product)
        critical_hazards = [h for h in hazards if h.severity == "CRITICAL"]
        high_hazards = [h for h in hazards if h.severity in ["HIGH", "CRITICAL"]]

        # Determine overall verdict
        high_severity_count = sum(1 for c in contradictions if c.severity == "HIGH")
        if high_severity_count > 0:
            verdict = "UNHEALTHY / MISLEADING"
        elif critical_hazards:
            verdict = "UNHEALTHY (CRITICAL NUTRITIONAL LOAD)"
        elif len(contradictions) > 0 or high_hazards or len(disguised) > 0:
            verdict = "CAUTION (HIGH SUGAR / FAT / SODIUM)" if high_hazards else "CAUTION"
        elif nova >= 4:
            verdict = "CAUTION (ULTRA-PROCESSED UPF)"
        else:
            verdict = "CLEAN"
            
        # Build plain-English summary
        if verdict == "UNHEALTHY / MISLEADING":
            summary = (
                f"NutriPure AI flagged {len(contradictions)} deceptive claims on {product.product_name}. "
                f"The product is classified as NOVA Group {nova} (Ultra-Processed). "
                f"Front-of-pack claims contradict verified ingredient disclosures under FSSAI regulations."
            )
        elif verdict == "UNHEALTHY (CRITICAL NUTRITIONAL LOAD)":
            hazard_headlines = ", ".join([h.headline for h in critical_hazards])
            summary = (
                f"{product.product_name} exceeds critical WHO & ICMR-NIN safety limits: {hazard_headlines}. "
                f"Even without deceptive marketing claims on the front label, the nutrient concentration poses significant clinical metabolic hazards."
            )
        elif "CAUTION" in verdict:
            summary = (
                f"{product.product_name} contains elevated nutritional loads or industrial additives ({', '.join(disguised) if disguised else 'UPF additives'}). "
                f"Consumer caution advised for daily consumption."
            )
        else:
            summary = (
                f"{product.product_name} passed all deceptive marketing audits and nutritional hazard screenings. "
                f"Classified as NOVA Group {nova} (Minimally Processed) with clean ingredient integrity."
            )

        nova_exp = generate_nova_explanation(nova, product, decoded, disguised)
            
        report = AuditReport(
            product_id=product.id,
            product_name=product.product_name,
            brand=product.brand or "Unknown Brand",
            overall_health_verdict=verdict,
            nova_group=nova,
            deceptive_claims_count=len(contradictions),
            contradictions=contradictions,
            flagged_additives=decoded,
            disguised_sugars_found=disguised,
            nutritional_hazards=hazards,
            nova_explanation=nova_exp,
            executive_summary=summary
        )
        
        return {
            "overall_verdict": verdict,
            "executive_summary": summary,
            "audit_report": report
        }

    # ---------------------------------------------------------
    # Graph Assembly
    # ---------------------------------------------------------
    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        
        # Add Nodes
        graph.add_node("decode_chemicals", self.node_decode_chemicals)
        graph.add_node("regulatory_rag", self.node_regulatory_rag)
        graph.add_node("claim_grader", self.node_claim_contradiction_grader)
        graph.add_node("nova_scorer", self.node_toxicity_and_nova_scorer)
        graph.add_node("synthesize_report", self.node_synthesize_report)
        
        # Add Edges
        graph.add_edge(START, "decode_chemicals")
        graph.add_edge("decode_chemicals", "regulatory_rag")
        graph.add_edge("regulatory_rag", "claim_grader")
        graph.add_edge("claim_grader", "nova_scorer")
        
        # Add Conditional Edge (Reflection Loop)
        graph.add_conditional_edges(
            "nova_scorer",
            self.should_reflect,
            {
                "reflect_rag": "regulatory_rag",
                "synthesize": "synthesize_report"
            }
        )
        graph.add_edge("synthesize_report", END)
        
        return graph.compile()

    def run_audit(self, product: ProductInput) -> AuditReport:
        """Executes the full LangGraph state machine on a ProductInput object."""
        initial_state: AgentState = {
            "product": product,
            "decoded_additives": [],
            "disguised_sugars": [],
            "regulatory_citations": [],
            "mcp_alerts": [],
            "contradictions": [],
            "nova_group": 0,
            "overall_verdict": "",
            "executive_summary": "",
            "reflection_count": 0,
            "quality_passed": False,
            "audit_report": None
        }
        
        final_state = self.workflow.invoke(initial_state)
        return final_state["audit_report"]


# Alias for brand alignment
NutriPureGraph = NutriAuditGraph


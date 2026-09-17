"""
Human-in-the-Loop (HITL) Checkpointing & Personalized Health Gating.
Implements LangGraph state persistence using SqliteSaver and interrupt()
to adapt food audit verdicts to individual medical constraints.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver

from src.schemas import (
    ProductInput,
    DecodedAdditive,
    ContradictionItem,
    AuditReport,
    ClaimAdjudication,
    HITLAdjudicationPayload,
)
from src.chemical_decoder import ChemicalDecoder
from src.extractor import detect_disguised_sugars
from src.rag_engine import RegulatoryRAG
from src.mcp_tools import MCPToolRegistry
from src.graph import AgentState, evaluate_marketing_claims
from src.nutrition_hazards import evaluate_nutritional_hazards, generate_nova_explanation


class UserHealthProfile(BaseModel):
    """Personalized medical profile supplied by the human user during HITL review."""
    diabetic: bool = Field(default=False, description="User has Type 1 or Type 2 Diabetes")
    hypertensive: bool = Field(default=False, description="User has High Blood Pressure / Sodium sensitivity")
    allergies: List[str] = Field(default_factory=list, description="Allergens (e.g. Gluten, Soy, Peanuts, Lactose)")
    is_child: bool = Field(default=False, description="Product is intended for an infant or young child")
    pregnant: bool = Field(default=False, description="User is pregnant or nursing")


class PersonalizedSafetyAuditor:
    """Evaluates medical contraindications and detects dynamic contextual risk triggers."""
    
    @staticmethod
    def detect_dynamic_triggers(
        product: ProductInput,
        additives: List[DecodedAdditive],
        disguised_sugars: List[str]
    ) -> List[Dict[str, Any]]:
        """Identifies specific health risks in product formulation to present to the human during HITL review."""
        triggers = []
        nf = getattr(product, "nutritional_facts", None)
        total_sugar = nf.total_sugars_g if nf else 0.0
        sodium = nf.sodium_mg if nf else 0.0
        
        lower_ing = product.raw_ingredients_text.lower()
        has_sugar_ing = any(s in lower_ing for s in ["sugar", "sucrose", "glucose", "syrup", "jaggery", "honey"])
        
        # 1. Sugar trigger
        if (total_sugar and total_sugar > 10.0) or disguised_sugars or has_sugar_ing:
            sug_list = ", ".join(disguised_sugars) if disguised_sugars else ("Added Sugar in Ingredients" if has_sugar_ing else "None")
            sugar_amount_str = f"{total_sugar:.1f}g sugars/100g" if total_sugar else "Declared sugar ingredients"
            triggers.append({
                "condition_key": "diabetic",
                "label": "High Glycemic / Sugar Spike Risk",
                "question": "Is the intended consumer Diabetic, Pre-diabetic, or monitoring blood glucose?",
                "evidence": f"Contains {sugar_amount_str} and sweeteners: {sug_list}."
            })
        
        # 2. Gluten trigger
        if any(k in lower_ing for k in ["wheat", "maida", "atta", "gluten", "malt", "cereal extract"]):
            triggers.append({
                "condition_key": "allergy_gluten",
                "label": "Gluten / Wheat Detected",
                "question": "Does the consumer have Celiac disease or a Gluten / Wheat intolerance?",
                "evidence": "Product formulation contains wheat flour, maida, or gluten sources."
            })
            
        # 3. Soy trigger
        if any(k in lower_ing for k in ["soy", "soya"]) or any("322" in a.code for a in additives):
            triggers.append({
                "condition_key": "allergy_soy",
                "label": "Soy Derivative Detected",
                "question": "Does the consumer have a Soy allergy?",
                "evidence": "Contains soy lecithin or soya derivatives."
            })
            
        # 4. Dairy trigger
        if any(k in lower_ing for k in ["milk", "dairy", "whey", "lactose", "casein"]):
            triggers.append({
                "condition_key": "allergy_dairy",
                "label": "Dairy / Lactose Detected",
                "question": "Is the consumer Lactose Intolerant or Dairy-Allergic?",
                "evidence": "Contains milk solids, whey, or dairy components."
            })
            
        # 5. Pediatric trigger
        pediatric_additives = [
            a for a in additives 
            if a.category in ["Artificial Sweetener", "Synthetic Food Color"] or "Children" in a.contraindications
        ]
        if pediatric_additives:
            names = ", ".join([f"{a.chemical_name} ({a.code})" for a in pediatric_additives])
            triggers.append({
                "condition_key": "is_child",
                "label": "Synthetic Additives / Sweeteners Restricted for Children",
                "question": "Is this food intended for an infant or young child?",
                "evidence": f"Contains additives restricted/cautioned under WHO/EFSA pediatric guidelines: {names}."
            })
            
        # 6. Sodium trigger
        if sodium and sodium > 300.0:
            triggers.append({
                "condition_key": "hypertensive",
                "label": "Elevated Sodium Load",
                "question": "Is the consumer Hypertensive or on a medically restricted low-sodium diet?",
                "evidence": f"Contains {sodium:.0f}mg sodium per 100g."
            })
            
        return triggers

    @staticmethod
    def evaluate(
        profile: UserHealthProfile,
        additives: List[DecodedAdditive],
        disguised_sugars: List[str],
        product: ProductInput
    ) -> List[str]:
        alerts = []
        lower_ingredients = product.raw_ingredients_text.lower()
        nf = getattr(product, "nutritional_facts", None)
        
        # 1. Diabetic Constraints
        if profile.diabetic:
            for sugar in disguised_sugars:
                if sugar.lower() in ["maltodextrin", "liquid glucose", "invert sugar syrup", "high fructose corn syrup"]:
                    alerts.append(
                        f"DIABETES ALERT: Contains {sugar} with a Glycemic Index (GI > 100) higher than table sugar. "
                        f"Will induce rapid postprandial glycemic spikes."
                    )
            if nf and nf.total_sugars_g and nf.total_sugars_g > 10.0:
                alerts.append(
                    f"DIABETES ALERT: High total sugar content ({nf.total_sugars_g}g per 100g) "
                    f"exceeds safe glycemic thresholds."
                )
            elif any(s in lower_ingredients for s in ["sugar", "sucrose", "glucose", "syrup"]):
                alerts.append(
                    "DIABETES ALERT: Product formulation contains added sugars / syrups. Contraindicated for diabetic consumers."
                )

        # 2. Allergy Constraints
        for allergen in profile.allergies:
            all_lower = allergen.lower()
            if all_lower in ["gluten", "wheat"]:
                if any(k in lower_ingredients for k in ["wheat", "maida", "atta", "gluten", "malt", "cereal extract"]):
                    alerts.append("ALLERGY WARNING: Product contains GLUTEN/WHEAT ingredients. Unsafe for Celiac/Allergic consumer.")
            elif all_lower in ["soy", "soya"]:
                if "soy" in lower_ingredients or any("322" in a.code for a in additives):
                    alerts.append("ALLERGY WARNING: Contains SOY derivatives (Soy Lecithin / Soya Protein).")
            elif all_lower in ["dairy", "milk", "lactose"]:
                if any(k in lower_ingredients for k in ["milk", "whey", "lactose", "casein"]):
                    alerts.append("ALLERGY WARNING: Contains DAIRY/LACTOSE solids.")

        # 3. Child & Pediatric Safety
        if profile.is_child:
            for a in additives:
                if a.category in ["Artificial Sweetener", "Synthetic Food Color"] or "Children" in a.contraindications:
                    alerts.append(
                        f"PEDIATRIC WARNING: Additive {a.chemical_name} ({a.code}) is not recommended for children under WHO/EFSA guidelines."
                    )

        # 4. Hypertensive Constraints
        if profile.hypertensive and nf and nf.sodium_mg:
            if nf.sodium_mg > 300.0:
                alerts.append(
                    f"HYPERTENSION WARNING: High sodium load ({nf.sodium_mg}mg per 100g) "
                    f"exceeds low-sodium diet recommendations."
                )

        return alerts


class NutriAuditHITLGraph:
    """
    LangGraph Workflow with SqliteSaver Checkpointing and HITL interrupt().
    Allows interactive pausing before synthesis for human claim adjudication and contextual health gating.
    """

    def __init__(
        self,
        db_path: str = "data/audit_checkpoints.db",
        rag_engine: Optional[RegulatoryRAG] = None,
        chemical_decoder: Optional[ChemicalDecoder] = None,
        mcp_registry: Optional[MCPToolRegistry] = None
    ):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(conn=self.conn)
        self.checkpointer.setup()
        
        self.rag = rag_engine or RegulatoryRAG()
        self.decoder = chemical_decoder or ChemicalDecoder()
        self.mcp = mcp_registry or MCPToolRegistry()
        
        self.app = self._build_hitl_graph()

    def node_decode_chemicals(self, state: AgentState) -> Dict[str, Any]:
        product = state["product"]
        decoded = self.decoder.decode_all(product)
        disguised = detect_disguised_sugars(product.raw_ingredients_text)
        return {"decoded_additives": decoded, "disguised_sugars": disguised}

    def node_regulatory_rag(self, state: AgentState) -> Dict[str, Any]:
        product = state["product"]
        citations = []
        for claim in product.front_claims:
            v = self.rag.verify_marketing_claim(claim, product.raw_ingredients_text)
            for c in v["citations"]:
                if c not in citations:
                    citations.append(c)
        return {"regulatory_citations": citations}

    def node_claim_grader(self, state: AgentState) -> Dict[str, Any]:
        product = state["product"]
        decoded = state.get("decoded_additives", [])
        disguised = state.get("disguised_sugars", [])
        citations = state.get("regulatory_citations", [])
        contradictions = evaluate_marketing_claims(product, decoded, disguised, citations)
        return {"contradictions": contradictions}

    def node_hitl_checkpoint(self, state: AgentState) -> Dict[str, Any]:
        """
        Interactive Human-in-the-Loop Node.
        Halts the graph and yields control to the human user to adjudicate marketing violations
        and provide specific contextual health gating inputs.
        """
        product = state["product"]
        decoded_additives = state["decoded_additives"]
        disguised_sugars = state["disguised_sugars"]
        contradictions = state["contradictions"]
        
        dynamic_triggers = PersonalizedSafetyAuditor.detect_dynamic_triggers(
            product=product,
            additives=decoded_additives,
            disguised_sugars=disguised_sugars
        )
        
        contradictions_data = [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in contradictions
        ]
        
        # interrupt() pauses the graph and saves state to SQLite
        user_response = interrupt({
            "prompt": "Human-in-the-Loop Compliance & Health Adjudication Gate",
            "product_name": product.product_name,
            "brand": product.brand,
            "contradictions": contradictions_data,
            "detected_additives_count": len(decoded_additives),
            "disguised_sugars": disguised_sugars,
            "dynamic_health_triggers": dynamic_triggers,
        })
        
        claim_overrides: Dict[str, str] = {}
        expert_notes = None
        auditor_directive = "CONFIRM_FINDINGS"
        profile = UserHealthProfile()
        
        if isinstance(user_response, HITLAdjudicationPayload):
            for ca in user_response.claim_adjudications:
                claim_overrides[ca.claim] = ca.decision
            if user_response.health_profile:
                profile = UserHealthProfile(**user_response.health_profile)
            auditor_directive = user_response.auditor_directive
            expert_notes = user_response.expert_notes
            hitl_payload = user_response
        elif isinstance(user_response, dict):
            cas = user_response.get("claim_adjudications", [])
            for ca in cas:
                if isinstance(ca, dict):
                    claim_overrides[ca.get("claim", "")] = ca.get("decision", "CONFIRMED")
            hp = user_response.get("health_profile")
            if hp and isinstance(hp, dict):
                profile = UserHealthProfile(**hp)
            elif "diabetic" in user_response or "allergies" in user_response:
                profile = UserHealthProfile(**{k: v for k, v in user_response.items() if k in UserHealthProfile.model_fields})
            auditor_directive = user_response.get("auditor_directive", "CONFIRM_FINDINGS")
            expert_notes = user_response.get("expert_notes")
            hitl_payload = HITLAdjudicationPayload(
                claim_adjudications=[
                    ClaimAdjudication(claim=c, decision=d) for c, d in claim_overrides.items()
                ],
                health_profile=profile.model_dump(),
                auditor_directive=auditor_directive,
                expert_notes=expert_notes
            )
        elif isinstance(user_response, UserHealthProfile):
            profile = user_response
            hitl_payload = HITLAdjudicationPayload(
                health_profile=profile.model_dump(),
                auditor_directive="CONFIRM_FINDINGS"
            )
        else:
            hitl_payload = HITLAdjudicationPayload()
            
        # Apply human claim adjudications
        final_contradictions: List[ContradictionItem] = []
        for c in contradictions:
            override = claim_overrides.get(c.claim, "CONFIRMED")
            if override == "DISMISSED":
                # Human dismissed this violation -> exclude from report
                continue
            elif override == "ADVISORY":
                # Downgrade to advisory warning
                final_contradictions.append(ContradictionItem(
                    claim=c.claim,
                    contradiction_type="ADVISORY_NOTICE",
                    evidence=f"[Human Auditor Advisory] {c.evidence}",
                    severity="LOW",
                    relevant_regulation=c.relevant_regulation
                ))
            else:
                final_contradictions.append(c)
                
        alerts = PersonalizedSafetyAuditor.evaluate(
            profile=profile,
            additives=decoded_additives,
            disguised_sugars=disguised_sugars,
            product=product
        )
        
        return {
            "contradictions": final_contradictions,
            "user_health_alerts": alerts,
            "hitl_payload": hitl_payload,
            "is_human_verified": True
        }

    def node_synthesize(self, state: AgentState) -> Dict[str, Any]:
        product = state["product"]
        contradictions = state["contradictions"]
        alerts = state.get("user_health_alerts", [])
        hitl_payload = state.get("hitl_payload")
        
        directive = hitl_payload.auditor_directive if hitl_payload else "CONFIRM_FINDINGS"
        expert_notes = hitl_payload.expert_notes if hitl_payload else None
        
        # Evaluate independent WHO/ICMR-NIN nutritional hazards
        hazards = evaluate_nutritional_hazards(product)
        critical_hazards = [h for h in hazards if h.severity == "CRITICAL"]
        high_hazards = [h for h in hazards if h.severity in ["HIGH", "CRITICAL"]]

        if directive == "CLEAR_COMPLIANT":
            verdict = "CLEAN (HUMAN CERTIFIED)"
            nova = 1
        elif directive == "ISSUE_WARNING":
            verdict = "UNHEALTHY / MISLEADING (OFFICIAL WARNING)"
            nova = 4
        elif len(contradictions) > 0:
            verdict = "UNHEALTHY / MISLEADING"
            nova = 4
        elif critical_hazards:
            verdict = "UNHEALTHY (CRITICAL NUTRITIONAL LOAD)"
            nova = 4
        elif len(alerts) > 0 or high_hazards or len(state["disguised_sugars"]) > 0:
            verdict = "CAUTION (HIGH SUGAR / FAT / SODIUM)" if high_hazards else "CAUTION"
            nova = 4
        elif len(state["decoded_additives"]) > 0:
            verdict = "CAUTION (ULTRA-PROCESSED UPF)"
            nova = 4
        else:
            verdict = "CLEAN"
            nova = 1
            
        summary_parts = [
            f"Autonomous audit cross-referenced against FSSAI & WHO standards with interactive Human-in-the-Loop adjudication.",
            f"Identified {len(contradictions)} active marketing claim contradiction(s) and {len(alerts)} personalized health contraindication(s)."
        ]
        if critical_hazards:
            summary_parts.append(
                f"Nutritional Safety Alert: Product contains dangerous nutrient levels exceeding WHO/ICMR-NIN safety limits ({critical_hazards[0].headline})."
            )
        if expert_notes:
            summary_parts.append(f"Expert Food Safety Officer Directive: \"{expert_notes}\"")

        nova_exp = generate_nova_explanation(nova, product, state["decoded_additives"], state["disguised_sugars"])
            
        report = AuditReport(
            product_id=product.id,
            product_name=product.product_name,
            brand=product.brand or "Unknown Brand",
            overall_health_verdict=verdict,
            nova_group=nova,
            deceptive_claims_count=len(contradictions),
            contradictions=contradictions,
            flagged_additives=state["decoded_additives"],
            disguised_sugars_found=state["disguised_sugars"],
            nutritional_hazards=hazards,
            nova_explanation=nova_exp,
            user_health_alerts=alerts,
            executive_summary=" ".join(summary_parts),
            is_human_verified=True,
            hitl_adjudication=hitl_payload
        )
        return {"audit_report": report}

    def _build_hitl_graph(self) -> Any:
        graph = StateGraph(AgentState)
        
        graph.add_node("decode_chemicals", self.node_decode_chemicals)
        graph.add_node("regulatory_rag", self.node_regulatory_rag)
        graph.add_node("claim_grader", self.node_claim_grader)
        graph.add_node("hitl_checkpoint", self.node_hitl_checkpoint)
        graph.add_node("synthesize", self.node_synthesize)
        
        graph.add_edge(START, "decode_chemicals")
        graph.add_edge("decode_chemicals", "regulatory_rag")
        graph.add_edge("regulatory_rag", "claim_grader")
        graph.add_edge("claim_grader", "hitl_checkpoint")
        graph.add_edge("hitl_checkpoint", "synthesize")
        graph.add_edge("synthesize", END)
        
        return graph.compile(checkpointer=self.checkpointer)

    def start_audit(self, product: ProductInput, thread_id: str = "default_audit") -> Dict[str, Any]:
        """Runs the LangGraph workflow up to the HITL interruption gate."""
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: AgentState = {
            "product": product,
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
            "audit_report": None,
            "hitl_payload": None,
            "is_human_verified": False
        }
        
        # Stream until interrupt
        for _ in self.app.stream(initial_state, config=config):
            pass
            
        snapshot = self.app.get_state(config)
        if snapshot.tasks and snapshot.tasks[0].interrupts:
            return {
                "status": "INTERRUPTED",
                "interrupt_payload": snapshot.tasks[0].interrupts[0].value,
                "state_values": snapshot.values
            }
        else:
            return {
                "status": "COMPLETED",
                "audit_report": snapshot.values.get("audit_report")
            }

    def resume_audit(self, adjudication_input: Any, thread_id: str = "default_audit") -> AuditReport:
        """Resumes the interrupted LangGraph workflow with human adjudication input."""
        config = {"configurable": {"thread_id": thread_id}}
        for _ in self.app.stream(Command(resume=adjudication_input), config=config):
            pass
        snapshot = self.app.get_state(config)
        return snapshot.values["audit_report"]


# Alias for brand alignment
NutriPureHITLGraph = NutriAuditHITLGraph


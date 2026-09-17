"""
Pydantic Data Models for NutriPure AI.
Defines schemas for product inputs, extracted ingredients, additives,
and final audit reports.
"""

import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class NutritionalFacts(BaseModel):
    """Nutritional breakdown per 100g or 100ml of product."""
    energy_kcal: Optional[float] = Field(default=None, description="Energy in kcal per 100g")
    protein_g: Optional[float] = Field(default=None, description="Protein in grams per 100g")
    carbohydrates_g: Optional[float] = Field(default=None, description="Total carbohydrates in grams")
    total_sugars_g: Optional[float] = Field(default=None, description="Total sugars in grams per 100g")
    added_sugars_g: Optional[float] = Field(default=0.0, description="Added industrial sugars in grams")
    dietary_fiber_g: Optional[float] = Field(default=None, description="Dietary fiber in grams")
    total_fat_g: Optional[float] = Field(default=None, description="Total fat in grams")
    saturated_fat_g: Optional[float] = Field(default=None, description="Saturated fat in grams")
    trans_fat_g: Optional[float] = Field(default=0.0, description="Trans fatty acids in grams")
    sodium_mg: Optional[float] = Field(default=None, description="Sodium content in milligrams")
    cholesterol_mg: Optional[float] = Field(default=None, description="Cholesterol in milligrams")
    polyols_g: Optional[float] = Field(default=0.0, description="Sugar alcohols (polyols) in grams")
    serving_size: Optional[str] = Field(default=None, description="Serving size declaration, e.g. 30g")

    @field_validator(
        "energy_kcal", "protein_g", "carbohydrates_g", "total_sugars_g",
        "added_sugars_g", "dietary_fiber_g", "total_fat_g", "saturated_fat_g",
        "trans_fat_g", "sodium_mg", "cholesterol_mg", "polyols_g",
        mode="before"
    )
    @classmethod
    def clean_numeric_fields(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            clean_str = v.strip().lower()
            if clean_str in ["nil", "none", "na", "n/a", "trace", "-", ""]:
                return 0.0
            match = re.search(r'([0-9]+(?:\.[0-9]+)?)', clean_str)
            if match:
                return float(match.group(1))
        return None


class ExtractedIngredient(BaseModel):
    """Individual ingredient parsed from packaging text."""
    name: str = Field(..., description="Cleaned name of the ingredient")
    percentage: Optional[float] = Field(default=None, description="Declared percentage by weight if available")
    is_additive: bool = Field(default=False, description="True if this is an INS/E additive or artificial substance")
    ins_code: Optional[str] = Field(default=None, description="Associated INS or E code (e.g., INS 503(ii))")
    raw_text: str = Field(..., description="Raw text snippet from packaging")


class ProductInput(BaseModel):
    """Complete structured representation of a food product under audit."""
    id: str = Field(..., description="Unique product identifier or barcode")
    product_name: str = Field(..., description="Commercial name of the product")
    brand: Optional[str] = Field(default="Unknown Brand", description="Manufacturer or brand name")
    claimed_category: Optional[str] = Field(default="Packaged Food", description="Category advertised on packaging")
    front_claims: List[str] = Field(default_factory=list, description="Marketing claims highlighted on front of pack")
    raw_ingredients_text: str = Field(..., description="Full raw ingredient list as printed on the back")
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, description="Parsed structured ingredients")
    nutritional_facts: NutritionalFacts = Field(default_factory=NutritionalFacts, description="Nutritional facts per 100g")
    declared_ins_codes: List[str] = Field(default_factory=list, description="All INS/E-numbers detected on label")


class DecodedAdditive(BaseModel):
    """Detailed profile of a decoded chemical additive."""
    code: str = Field(..., description="INS or E-number code")
    chemical_name: str = Field(..., description="Standard chemical or IUPAC name")
    category: str = Field(..., description="Functional class (e.g., Preservative, Sweetener, Emulsifier)")
    risk_level: str = Field(..., description="Hazard rating: Safe, Low, Moderate, or High")
    description: str = Field(..., description="Function in food manufacturing")
    health_warnings: List[str] = Field(default_factory=list, description="Known adverse clinical effects")
    contraindications: List[str] = Field(default_factory=list, description="Medical conditions at high risk")
    is_disguised_sugar: bool = Field(default=False, description="True if used as an industrial sweetener/sugar substitute")


class NutritionalHazard(BaseModel):
    """Evaluation of toxic/dangerous nutrient concentrations based on WHO/ICMR-NIN thresholds."""
    nutrient: str = Field(..., description="Nutrient name, e.g. Added Sugar, Total Sugar, Trans Fat, Saturated Fat, Sodium")
    amount_per_100g: float = Field(..., description="Quantity found per 100g or 100ml")
    unit: str = Field(default="g", description="Unit of measurement (g, mg)")
    benchmark_threshold: float = Field(..., description="Maximum recommended safety threshold")
    severity: str = Field(..., description="CRITICAL, HIGH, or MODERATE")
    headline: str = Field(..., description="Short impactful summary (e.g., 'Excessive Sugar Load')")
    explanation: str = Field(..., description="Clinical risk explanation and benchmark authority citation")
    clinical_risk: Optional[str] = Field(default=None, description="Physiological health risk")
    guideline_source: str = Field(..., description="WHO 2015 Guideline / ICMR-NIN 2024 / FSSAI")


class NovaExplanation(BaseModel):
    """Transparent scientific explanation of NOVA Food Processing classification."""
    group: int = Field(..., description="NOVA Group (1 to 4)")
    group_name: str = Field(..., description="Official title of the NOVA group")
    definition: str = Field(..., description="Detailed definition of this processing group")
    classification_reasons: List[str] = Field(default_factory=list, description="Specific triggers in this product")
    triggering_substances: List[str] = Field(default_factory=list, description="Industrial additives, sweeteners, or markers")
    health_implications: str = Field(..., description="Documented epidemiological & clinical risks")


class ContradictionItem(BaseModel):
    """A detected clash between front marketing claims and back ingredients/nutrition."""
    claim: str = Field(..., description="The front-of-pack marketing claim (e.g., '100% Atta')")
    contradiction_type: str = Field(..., description="Classification: LEGAL_VIOLATION, MISLEADING, or HEALTH_HAZARD")
    evidence: str = Field(..., description="Back-of-pack evidence disproving the claim")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    relevant_regulation: Optional[str] = Field(default=None, description="FSSAI or WHO section violated")


class ClaimAdjudication(BaseModel):
    """Human expert adjudication for an individual marketing claim violation."""
    claim: str
    decision: str = Field(default="CONFIRMED", description="CONFIRMED (violation), ADVISORY (warning), or DISMISSED (allow)")
    human_notes: Optional[str] = None


class HITLAdjudicationPayload(BaseModel):
    """Comprehensive human adjudication input submitted during LangGraph HITL gate."""
    claim_adjudications: List[ClaimAdjudication] = Field(default_factory=list)
    health_profile: Optional[Dict[str, Any]] = None
    auditor_directive: str = Field(default="CONFIRM_FINDINGS", description="CONFIRM_FINDINGS, ISSUE_WARNING, or CLEAR_COMPLIANT")
    expert_notes: Optional[str] = None


class AuditReport(BaseModel):
    """Final comprehensive audit report for the consumer."""
    product_id: str
    product_name: str
    brand: str
    overall_health_verdict: str = Field(..., description="CLEAN, CAUTION, or UNHEALTHY / MISLEADING")
    nova_group: int = Field(..., description="NOVA Food Processing Group (1 to 4)")
    deceptive_claims_count: int = Field(default=0)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    flagged_additives: List[DecodedAdditive] = Field(default_factory=list)
    disguised_sugars_found: List[str] = Field(default_factory=list)
    nutritional_hazards: List[NutritionalHazard] = Field(default_factory=list, description="Independent hazards evaluated against WHO & ICMR-NIN limits")
    nova_explanation: Optional[NovaExplanation] = Field(default=None, description="Detailed breakdown of NOVA group rationale and clinical risks")
    user_health_alerts: List[str] = Field(default_factory=list, description="Personalized warnings based on medical profile")
    executive_summary: str = Field(..., description="Plain-English explanation for the consumer")
    is_human_verified: bool = Field(default=False, description="True if audited and finalized with Human-in-the-Loop review")
    hitl_adjudication: Optional[HITLAdjudicationPayload] = Field(default=None, description="Detailed records of human expert adjudication")



"""
Nutritional Hazards and NOVA Classification Engine for NutriPure AI.
Evaluates food formulations against authoritative scientific and public health benchmarks:
- WHO (World Health Organization) Guideline on Sugars Intake (2015)
- WHO REPLACE Initiative on Trans-Fatty Acids (2018-2023)
- ICMR-NIN (Indian Council of Medical Research - National Institute of Nutrition) Dietary Guidelines (2024)
- FSSAI (Food Safety and Standards Authority of India) Labelling and Display Regulations (2020)
- NOVA Food Classification System (Carlos Monteiro et al., University of Sao Paulo / FAO / WHO)
"""

from typing import List, Dict, Optional, Any
from src.schemas import ProductInput, DecodedAdditive, NutritionalHazard, NovaExplanation


WHO_DAILY_SUGAR_OPTIMAL_G = 25.0  # 6 teaspoons / day (~5% daily energy)
WHO_DAILY_SUGAR_MAX_G = 50.0      # 10% daily energy
THRESHOLD_SUGAR_CRITICAL_G = 22.5 # > 22.5g / 100g is classified as High Sugar (UK FSA / WHO)
THRESHOLD_SUGAR_HIGH_G = 10.0     # > 10g / 100g is elevated

THRESHOLD_TRANS_FAT_CRITICAL_G = 0.05  # Any detectable trans fat > 0g (WHO REPLACE)

THRESHOLD_SAT_FAT_CRITICAL_G = 8.0
THRESHOLD_SAT_FAT_HIGH_G = 4.0

WHO_DAILY_SODIUM_MAX_MG = 2000.0
THRESHOLD_SODIUM_CRITICAL_MG = 600.0
THRESHOLD_SODIUM_HIGH_MG = 300.0


NOVA_DEFINITIONS = {
    1: {
        "name": "Unprocessed or Minimally Processed Foods",
        "description": (
            "Natural edible parts of plants (seeds, fruits, leaves, roots) or animals (muscle, eggs, milk) "
            "obtained directly from nature or subjected to minimal physical processing (cleaning, portioning, "
            "drying, boiling, pasteurization, refrigeration, natural fermentation) without the addition of "
            "salt, sugar, oils, fats, or industrial chemical additives."
        ),
        "examples": "Fresh whole fruits, vegetables, whole rolled oats, raw nuts & seeds, fresh milk, pasteurized whole milk, natural pulses, lentils, whole grains, eggs, plain unsweetened curd.",
        "dietary_role": "Should form the primary foundation of a healthy, balanced human diet."
    },
    2: {
        "name": "Processed Culinary Ingredients",
        "description": (
            "Substances obtained directly from Group 1 foods or from nature by industrial processes such as "
            "pressing, refining, grinding, or extraction. They are rarely consumed alone and are used in home "
            "and restaurant kitchens to season, cook, and prepare Group 1 foods."
        ),
        "examples": "Cold-pressed vegetable oils, butter, lard, table sugar (sucrose), jaggery, honey, rock salt, table salt, vinegar.",
        "dietary_role": "Use in small amounts for cooking and seasoning fresh whole foods."
    },
    3: {
        "name": "Processed Foods",
        "description": (
            "Relatively simple food products made by adding Group 2 ingredients (salt, sugar, oil) to Group 1 "
            "foods to increase their shelf-life or enhance their culinary qualities. Typically composed of "
            "2 or 3 ingredients that are still recognizable as food."
        ),
        "examples": "Canned vegetables in brine, freshly baked artisan bread (flour, water, yeast, salt), cheeses made from milk and salt, salted nuts, canned tuna in oil, simple cured meats.",
        "dietary_role": "Can be consumed as part of balanced meals in moderation."
    },
    4: {
        "name": "Ultra-Processed Foods (UPFs)",
        "description": (
            "Industrial formulations typically manufactured with 5 or more ingredients, containing substances "
            "never or rarely used in domestic kitchens (such as high-fructose corn syrup, hydrogenated or "
            "interesterified oils, maltodextrin, protein isolates) and cosmetic additives (artificial flavors, "
            "flavor enhancers, synthetic food colors, non-nutritive artificial sweeteners, emulsifiers, texturizers, "
            "and carbonating agents). These products are engineered to be hyper-palatable, highly profitable, "
            "and shelf-stable, often replacing fresh whole foods."
        ),
        "examples": "Commercial biscuits & cookies, packaged chips & crisps, reconstituted fruit juices with added sugar, mass-produced sliced white bread, instant noodles, sodas & energy drinks, reconstituted meat nuggets, sweetened breakfast cereals, packaged protein bars with artificial sweeteners.",
        "dietary_role": "Should be strictly minimized or avoided. Clinically linked to adverse metabolic and chronic health outcomes."
    }
}


def evaluate_nutritional_hazards(product: ProductInput) -> List[NutritionalHazard]:
    hazards: List[NutritionalHazard] = []
    nf = product.nutritional_facts
    if not nf:
        return hazards

    # 1. Total Sugars Audit
    if nf.total_sugars_g is not None:
        sugar = nf.total_sugars_g
        if sugar >= THRESHOLD_SUGAR_CRITICAL_G:
            pct_who_optimal = (sugar / WHO_DAILY_SUGAR_OPTIMAL_G) * 100.0
            pct_who_max = (sugar / WHO_DAILY_SUGAR_MAX_G) * 100.0
            hazards.append(NutritionalHazard(
                nutrient="Total Sugars",
                amount_per_100g=round(sugar, 1),
                unit="g",
                benchmark_threshold=THRESHOLD_SUGAR_CRITICAL_G,
                severity="CRITICAL",
                headline=f"Excessive Sugar Hazard ({sugar:.1f}g per 100g)",
                explanation=(
                    f"A 100g portion delivers {sugar:.1f}g of sugar ({sugar:.0f}% of product weight). "
                    f"This exhausts {pct_who_optimal:.0f}% of the WHO recommended daily optimal ceiling (25g/day) "
                    f"and {pct_who_max:.0f}% of the maximum ceiling (50g/day) in a single snack."
                ),
                clinical_risk="Rapid blood glucose spike, reactive hyperinsulinemia, increased risk of visceral fat accumulation, metabolic syndrome, and non-alcoholic fatty liver disease (NAFLD).",
                guideline_source="WHO Guideline on Sugars Intake (2015) & UK FSA High Sugar Benchmark (>22.5g/100g)"
            ))
        elif sugar >= THRESHOLD_SUGAR_HIGH_G:
            pct_who_optimal = (sugar / WHO_DAILY_SUGAR_OPTIMAL_G) * 100.0
            hazards.append(NutritionalHazard(
                nutrient="Total Sugars",
                amount_per_100g=round(sugar, 1),
                unit="g",
                benchmark_threshold=THRESHOLD_SUGAR_HIGH_G,
                severity="HIGH",
                headline=f"Elevated Sugar Content ({sugar:.1f}g per 100g)",
                explanation=(
                    f"Contains {sugar:.1f}g of sugar per 100g, supplying {pct_who_optimal:.0f}% of the daily "
                    f"WHO optimal sugar allowance (25g/day)."
                ),
                clinical_risk="Contributes to elevated glycemic load; caution recommended for pre-diabetic and weight-conscious individuals.",
                guideline_source="WHO Guideline on Sugars Intake (2015) & ICMR-NIN 2024"
            ))

    # 2. Refined Added Sugars Audit
    if nf.added_sugars_g and nf.added_sugars_g >= 10.0:
        added = nf.added_sugars_g
        hazards.append(NutritionalHazard(
            nutrient="Added Sugars",
            amount_per_100g=round(added, 1),
            unit="g",
            benchmark_threshold=10.0,
            severity="HIGH" if added < 20.0 else "CRITICAL",
            headline=f"High Refined Added Sugars ({added:.1f}g per 100g)",
            explanation=(
                f"Contains {added:.1f}g of refined added sugars (sucrose, syrups, or concentrates) "
                f"which provide empty calories devoid of dietary fiber or micronutrients."
            ),
            clinical_risk="Promotes dental caries, elevates hepatic de novo lipogenesis, and impairs long-term insulin sensitivity.",
            guideline_source="ICMR-NIN Dietary Guidelines for Indians (2024) & FSSAI Labelling Regulations"
        ))

    # 3. Trans Fatty Acids Audit (WHO REPLACE Standard)
    if nf.trans_fat_g is not None and nf.trans_fat_g >= THRESHOLD_TRANS_FAT_CRITICAL_G:
        tf = nf.trans_fat_g
        hazards.append(NutritionalHazard(
            nutrient="Trans Fat",
            amount_per_100g=round(tf, 2),
            unit="g",
            benchmark_threshold=0.0,
            severity="CRITICAL",
            headline=f"Dangerous Trans Fat Detected ({tf:.2f}g per 100g)",
            explanation=(
                f"Product contains {tf:.2f}g of trans fatty acids per 100g. "
                f"According to WHO and global cardiological consensus, there is NO safe level of industrial trans fat."
            ),
            clinical_risk="Dramatically increases atherogenic LDL cholesterol, depresses protective HDL, induces systemic vascular endothelial dysfunction, and elevates coronary heart disease risk.",
            guideline_source="WHO REPLACE Global Action Package & FSSAI Trans Fat Elimination Regulation (2022)"
        ))

    # 4. Saturated Fatty Acids Audit
    if nf.saturated_fat_g is not None:
        sat_fat = nf.saturated_fat_g
        if sat_fat >= THRESHOLD_SAT_FAT_CRITICAL_G:
            hazards.append(NutritionalHazard(
                nutrient="Saturated Fat",
                amount_per_100g=round(sat_fat, 1),
                unit="g",
                benchmark_threshold=THRESHOLD_SAT_FAT_CRITICAL_G,
                severity="CRITICAL",
                headline=f"Excessive Saturated Fat Load ({sat_fat:.1f}g per 100g)",
                explanation=(
                    f"Contains {sat_fat:.1f}g of saturated fat per 100g. Often derived from low-cost refined palm oil "
                    f"or fractionated vegetable fats, supplying over 40-50% of the maximum daily allowance in 100g."
                ),
                clinical_risk="Elevates plasma LDL-C and apolipoprotein B, accelerating arterial atherosclerosis and cardiovascular morbidity.",
                guideline_source="ICMR-NIN 2024 & WHO Saturated Fat Intake Recommendations (<10% total calories)"
            ))
        elif sat_fat >= THRESHOLD_SAT_FAT_HIGH_G:
            hazards.append(NutritionalHazard(
                nutrient="Saturated Fat",
                amount_per_100g=round(sat_fat, 1),
                unit="g",
                benchmark_threshold=THRESHOLD_SAT_FAT_HIGH_G,
                severity="HIGH",
                headline=f"High Saturated Fat Content ({sat_fat:.1f}g per 100g)",
                explanation=f"Contains {sat_fat:.1f}g of saturated fat per 100g, exceeding the recommended healthy threshold of 4.0g/100g.",
                clinical_risk="Regular consumption contributes to elevated circulating cholesterol and atherogenic dyslipidemia.",
                guideline_source="ICMR-NIN 2024 Guidelines & UK FSA Saturated Fat Profile"
            ))

    # 5. Sodium / Salt Audit
    if nf.sodium_mg is not None:
        sodium = nf.sodium_mg
        if sodium >= THRESHOLD_SODIUM_CRITICAL_MG:
            pct_who_sodium = (sodium / WHO_DAILY_SODIUM_MAX_MG) * 100.0
            hazards.append(NutritionalHazard(
                nutrient="Sodium",
                amount_per_100g=round(sodium, 0),
                unit="mg",
                benchmark_threshold=THRESHOLD_SODIUM_CRITICAL_MG,
                severity="CRITICAL",
                headline=f"Critical High Sodium Load ({sodium:.0f}mg per 100g)",
                explanation=(
                    f"Contains {sodium:.0f}mg of sodium per 100g. A single 100g serving depletes {pct_who_sodium:.0f}% "
                    f"of the WHO recommended maximum daily limit (2000mg/day)."
                ),
                clinical_risk="Induces fluid retention, arterial wall stiffness, elevated systemic blood pressure (hypertension), and increased renal filtration stress.",
                guideline_source="WHO 2020 Sodium Guideline & ICMR-NIN 2024 Upper Tolerable Intake"
            ))
        elif sodium >= THRESHOLD_SODIUM_HIGH_MG:
            hazards.append(NutritionalHazard(
                nutrient="Sodium",
                amount_per_100g=round(sodium, 0),
                unit="mg",
                benchmark_threshold=THRESHOLD_SODIUM_HIGH_MG,
                severity="HIGH",
                headline=f"Elevated Sodium Level ({sodium:.0f}mg per 100g)",
                explanation=f"Contains {sodium:.0f}mg sodium per 100g, higher than the recommended 300mg/100g benchmark.",
                clinical_risk="May adversely affect hypertensive individuals and individuals monitoring electrolyte balance.",
                guideline_source="WHO 2020 Guideline on Sodium Intake"
            ))

    return hazards


def generate_nova_explanation(
    nova_group: int,
    product: ProductInput,
    decoded_additives: List[DecodedAdditive],
    disguised_sugars: List[str]
) -> NovaExplanation:
    info = NOVA_DEFINITIONS.get(nova_group, NOVA_DEFINITIONS[4])
    reasons: List[str] = []
    triggering_substances: List[str] = []

    for a in decoded_additives:
        item = f"{a.chemical_name} ({a.code}) [{a.category}]"
        triggering_substances.append(item)

    for s in disguised_sugars:
        item = f"Disguised / Industrial Sweetener: {s}"
        if item not in triggering_substances:
            triggering_substances.append(item)

    lower_raw = product.raw_ingredients_text.lower()
    industrial_markers = [
        ("palm oil", "Refined / Fractionated Palm Oil"),
        ("invert sugar", "Invert Sugar Syrup"),
        ("maltodextrin", "Maltodextrin (Hydrolyzed Starch)"),
        ("high fructose", "High Fructose Corn Syrup"),
        ("hydrogenated", "Hydrogenated / Hardened Vegetable Oil"),
        ("artificial flavour", "Artificial Flavouring Substances"),
        ("nature identical flavour", "Nature Identical Flavouring Agents"),
        ("soy lecithin", "Soy Lecithin (Industrial Emulsifier)"),
        ("polydextrose", "Synthetic Prebiotic Texturizer (Polydextrose)")
    ]
    for key, label in industrial_markers:
        if key in lower_raw and label not in triggering_substances:
            triggering_substances.append(label)

    ing_count = len(product.ingredients)
    if nova_group == 4:
        reasons.append(f"Product is an industrial formulation containing {ing_count} parsed ingredients.")
        if decoded_additives:
            reasons.append(f"Contains {len(decoded_additives)} chemical additive(s) (preservatives, emulsifiers, synthetic colors, or leaveners).")
        if disguised_sugars:
            reasons.append(f"Contains {len(disguised_sugars)} disguised industrial sugar/sweetener substitute(s).")
        if any("flavour" in s.lower() for s in triggering_substances):
            reasons.append("Formulation utilizes cosmetic artificial/nature-identical flavorings to engineer hyper-palatability.")
        health_imp = (
            "Consuming Ultra-Processed Foods (UPFs) regularly is clinically linked to adverse health outcomes "
            "(BMJ 2024 umbrella review): elevated risk of cardiovascular disease (+50%), type 2 diabetes (+40%), "
            "obesity, altered gut microbiome integrity (mucus layer erosion from emulsifiers), and systemic low-grade inflammation."
        )
    elif nova_group == 3:
        reasons.append("Product contains simple whole ingredients with added culinary salt, sugar, or oil.")
        reasons.append("No industrial synthetic additives, non-sugar sweeteners, or deconstructed starches detected.")
        health_imp = "Processed foods can be consumed in moderation as part of a balanced diet, keeping sodium and fat intake within recommended limits."
    elif nova_group == 2:
        reasons.append("Single extracted culinary ingredient (oil, sugar, salt, or fat) used for cooking.")
        health_imp = "Culinary ingredients are designed to be used in kitchen preparations in small amounts, not consumed as standalone meals."
    else:
        reasons.append("Single whole food or minimally processed natural substance with no added sugar, salt, oil, or chemicals.")
        reasons.append(f"Clean formulation containing {ing_count} whole ingredient(s).")
        health_imp = "Minimally processed whole foods provide maximum nutrient density, intact fiber matrix, and optimal metabolic satiety."

    return NovaExplanation(
        group=nova_group,
        group_name=info["name"],
        definition=info["description"],
        classification_reasons=reasons,
        triggering_substances=triggering_substances,
        health_implications=health_imp
    )

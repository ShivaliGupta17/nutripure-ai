# -*- coding: utf-8 -*-
"""
Plain-English Consumer Summary Generator
Translates complex food science, chemical INS codes, and regulatory legalities
into simple, honest, everyday language for ordinary shoppers and families.
"""
from typing import Dict, Any, List
from src.schemas import AuditReport, ProductInput


COMMON_ADDITIVES_PLAIN_EXPLANATIONS = {
    "319": ("TBHQ (Artificial Preservative)", "A synthetic chemical preservative that prevents oils and fats from going rancid over long shelf storage."),
    "320": ("BHA (Synthetic Preservative)", "An industrial chemical preservative used to prevent food from spoiling; flagged by health researchers."),
    "321": ("BHT (Synthetic Preservative)", "A chemical preservative added to keep fried snacks tasting fresh for months on a shelf."),
    "322": ("Lecithin (Emulsifier)", "A binder that prevents oils and water from separating, usually derived from soy or sunflower."),
    "471": ("Mono- and Diglycerides (Emulsifier)", "Processed fats used to improve softness, prevent staling, and keep baked goods moist."),
    "500": ("Baking Soda (Sodium Bicarbonate)", "A standard leavening agent that helps dough rise and gives a crisp texture."),
    "500(ii)": ("Baking Soda (Sodium Bicarbonate)", "A standard leavening agent that helps dough rise and gives a crisp texture."),
    "503": ("Ammonium Bicarbonate (Baker's Ammonia)", "A leavening agent used in crackers and biscuits to make them extra crisp."),
    "503(ii)": ("Ammonium Bicarbonate (Baker's Ammonia)", "A leavening agent used in crackers and biscuits to make them extra crisp."),
    "150d": ("Caramel IV (Ammonia Sulfite Caramel)", "An artificial dark brown food coloring made under chemical pressure; purely cosmetic."),
    "621": ("MSG (Monosodium Glutamate)", "A flavor enhancer that creates an intense savory, umami taste that encourages overeating."),
    "627": ("Disodium Guanylate (Flavor Enhancer)", "A chemical flavor booster often paired with MSG to amplify savory flavor."),
    "631": ("Disodium Inosinate (Flavor Enhancer)", "A chemical flavor booster used in salty snacks and instant noodles to boost taste intensity."),
    "635": ("Disodium 5-Ribonucleotides", "A powerful combination flavor enhancer commonly used in instant noodles and chips."),
    "955": ("Sucralose (Artificial Sweetener)", "A zero-calorie synthetic sweetener made by chlorinating sugar; 600 times sweeter than table sugar."),
    "951": ("Aspartame (Artificial Sweetener)", "An artificial low-calorie sweetener commonly found in diet drinks and sugar-free snacks."),
    "950": ("Acesulfame Potassium (Ace-K)", "A synthetic chemical sweetener often blended with other sweeteners to mask bitter aftertastes."),
    "211": ("Sodium Benzoate (Preservative)", "An industrial chemical preservative that stops mold and bacteria growth in liquids and sauces."),
    "202": ("Potassium Sorbate (Preservative)", "A chemical preservative used to stop yeast and fungal growth, extending shelf life."),
    "451": ("Sodium Triphosphate (Moisture Retainer)", "A chemical salt used to help processed foods hold water and maintain weight."),
    "412": ("Guar Gum (Thickener)", "A plant-derived gum used to thicken liquids and sauces and create a creamy mouthfeel."),
    "415": ("Xanthan Gum (Stabilizer)", "A fermented polysaccharide used to stabilize dressings and gluten-free doughs.")
}


def explain_chemical_in_plain_english(code: str, chemical_name: str, category: str) -> Dict[str, str]:
    """Translates an INS/E-number code into plain everyday terms."""
    clean_num = "".join(c for c in code if c.isdigit() or c in ["(", ")", "i", "v", "x"])
    digits_only = "".join(c for c in code if c.isdigit())
    
    match = COMMON_ADDITIVES_PLAIN_EXPLANATIONS.get(clean_num) or COMMON_ADDITIVES_PLAIN_EXPLANATIONS.get(digits_only)
    if match:
        friendly_name, simple_job = match
        return {
            "code": code,
            "friendly_name": friendly_name,
            "simple_job": simple_job
        }
    
    cat_lower = category.lower()
    if "preservative" in cat_lower or "antioxidant" in cat_lower:
        job = f"An artificial preservative ({chemical_name}) added to keep this food fresh for months on a store shelf."
    elif "sweetener" in cat_lower:
        job = f"An industrial sweetener ({chemical_name}) used instead of or alongside sugar."
    elif "color" in cat_lower:
        job = f"A chemical dye ({chemical_name}) added purely to give the food an artificial appearance."
    elif "emulsifier" in cat_lower or "stabilizer" in cat_lower:
        job = f"An additive ({chemical_name}) that keeps ingredients smoothly blended and prevents separation."
    elif "flavor" in cat_lower or "enhancer" in cat_lower:
        job = f"A flavor chemical ({chemical_name}) designed to stimulate taste receptors and make you crave more."
    else:
        job = f"An industrial food additive ({chemical_name}) used in factory food processing for texture or shelf life."
        
    return {
        "code": code,
        "friendly_name": chemical_name or code,
        "simple_job": job
    }


def simplify_contradiction(claim: str, evidence: str) -> str:
    """Translates a legalistic regulatory contradiction into simple everyday consumer speech."""
    claim_l = claim.lower()
    ev_l = evidence.lower()
    
    if "atta" in claim_l or "whole wheat" in claim_l:
        if "maida" in ev_l or "refined" in ev_l:
            return "The front of the pack boasts whole wheat (Atta), but the back label reveals it is mostly refined white flour (Maida), with only a small portion of whole wheat."
    
    if "fiber" in claim_l or "fibre" in claim_l:
        if "maida" in ev_l or "refined" in ev_l or "atta" in ev_l:
            return "The front advertises high dietary fiber, but the product is dominated by refined white flour (Maida) with only a minor portion of whole wheat, falling short of genuine high-fiber digestive benefits."

    if "trans fat" in claim_l:
        if "saturated" in ev_l or "palm" in ev_l:
            return "It advertises 'Zero Trans Fat', but it is loaded with heavy saturated fats from palm oil, which are still bad for your heart and arteries."
            
    if "rock salt" in claim_l or "ajwain" in claim_l or "rich in" in claim_l:
        if "%" in evidence or "1.2%" in evidence:
            return "It highlights traditional herbs or rock salt as hero ingredients, but they are added in tiny trace amounts (around 1%), while over 60% of the food is just plain white flour."
            
    if "pure" in claim_l or "fresh" in claim_l:
        if "ins" in ev_l or "preservative" in ev_l or "antioxidant" in ev_l or "tbhq" in ev_l or "319" in ev_l:
            return "The front says '100% Pure & Fresh', but it actually contains synthetic chemical preservatives (like INS 319) to stop factory fats from spoiling."
            
    if "sugar free" in claim_l or "no added sugar" in claim_l:
        if "maltodextrin" in ev_l or "invert" in ev_l or "syrup" in ev_l or "sweetener" in ev_l:
            return "Even though it says 'No Added Sugar', it uses hidden industrial syrups or artificial sweeteners that spike blood sugar or disrupt gut metabolism."
            
    # Default cleaner text
    clean_ev = evidence
    for prefix in ["The product violates", "Under FSSAI", "Section 7 of", "Reg 5:"]:
        if prefix in clean_ev:
            clean_ev = clean_ev.split(prefix)[0].strip()
    return clean_ev or "The ingredient formulation contradicts the front label marketing claims."


def generate_plain_english_summary(report: AuditReport, product: ProductInput) -> Dict[str, Any]:
    """
    Builds a complete, friendly, non-technical plain English translation
    of the entire audit report for everyday shoppers.
    """
    verdict = report.overall_health_verdict.upper()
    is_unhealthy = "UNHEALTHY" in verdict or "WARNING" in verdict
    is_caution = "CAUTION" in verdict
    is_clean = "CLEAN" in verdict and not is_unhealthy and not is_caution
    
    # 1. Headline & Bottom Line
    if is_unhealthy:
        headline = "🛑 Think Twice Before Eating: This is an Unhealthy Ultra-Processed Snack"
        headline_color = "#EF4444"
        bottom_line = (
            f"Despite the healthy claims printed on the front, {product.product_name} is "
            "heavily processed in an industrial factory. It is high in unhealthy fats, sodium, or refined sugars, "
            "and uses chemical additives to mask cheap core ingredients."
        )
    elif is_caution:
        headline = "⚠️ Eat In Moderation: Processed Food with Notable Health Concerns"
        headline_color = "#F59E0B"
        bottom_line = (
            f"{product.product_name} has some good qualities, but it is an ultra-processed product. "
            "It contains refined ingredients and industrial additives that you should not consume as an everyday staple."
        )
    else:
        headline = "✅ Wholesome & Honest: Safe for Everyday Consumption"
        headline_color = "#10B981"
        bottom_line = (
            f"{product.product_name} is a clean, honest product. What you see on the front matches what is inside, "
            "with real whole ingredients and zero deceptive marketing tricks."
        )
        
    # 2. Marketing Reality Checks
    marketing_truths = []
    for c in report.contradictions:
        plain_msg = simplify_contradiction(c.claim, c.evidence)
        marketing_truths.append({
            "claim": c.claim,
            "plain_truth": plain_msg,
            "severity": c.severity
        })
        
    # 3. What is Actually Inside (Primary Ingredients in Plain English)
    ingredients_plain = []
    lower_raw = product.raw_ingredients_text.lower()
    if "refined wheat flour" in lower_raw or "maida" in lower_raw:
        ingredients_plain.append("🍞 <b>Refined White Flour (Maida):</b> The primary ingredient. It has had its natural fiber and bran stripped away, meaning it digests rapidly and spikes blood sugar.")
    if "palm oil" in lower_raw or "hydrogenated" in lower_raw or "vegetable oil" in lower_raw:
        ingredients_plain.append("🛢️ <b>Industrial Cooking Oil (Palm/Vegetable Oil):</b> Heavy in saturated fats, which elevate LDL cholesterol and burden heart health when eaten frequently.")
    if "invert sugar" in lower_raw or "maltodextrin" in lower_raw or "liquid glucose" in lower_raw:
        ingredients_plain.append("🍯 <b>Disguised Factory Sugars:</b> Highly refined syrups that enter your bloodstream even faster than regular white sugar.")
    if "rock salt" in lower_raw or "edible salt" in lower_raw or "salt" in lower_raw:
        ingredients_plain.append("🧂 <b>High Salt Content:</b> Provides intense saltiness to enhance flavor and mask industrial processing.")
        
    # 4. Chemicals in Simple Words
    chemicals_plain = []
    for a in report.flagged_additives:
        chem_info = explain_chemical_in_plain_english(a.code, a.chemical_name, a.category)
        chemicals_plain.append(chem_info)
        
    # 5. Who Should Watch Out (Personal Health Impact)
    health_cautions = []
    nf = product.nutritional_facts
    if nf:
        if nf.sodium_mg and nf.sodium_mg >= 400:
            health_cautions.append(f"🧂 <b>High Blood Pressure / Heart Concerns:</b> Contains <b>{nf.sodium_mg:.0f}mg of sodium</b> per 100g. A single serving uses up a huge portion of your safe daily salt limit.")
        sugar_val = nf.total_sugars_g or nf.added_sugars_g or 0
        if sugar_val >= 10:
            health_cautions.append(f"🍬 <b>Diabetics & Pre-Diabetics:</b> Contains <b>{sugar_val:.1f}g of sugar</b> per 100g. It will cause a rapid spike in blood sugar.")
        if nf.saturated_fat_g and nf.saturated_fat_g >= 6:
            health_cautions.append(f"❤️ <b>Cholesterol & Heart Health:</b> Contains <b>{nf.saturated_fat_g:.1f}g of saturated fat</b> per 100g, mostly from industrial frying oils.")
            
    if report.nova_group == 4 and not health_cautions:
        health_cautions.append("🩺 <b>General Wellness:</b> Classified as an Ultra-Processed Food (UPF). Regular consumption is linked in clinical research to chronic low-grade gut inflammation.")
        
    # 6. Smart Swap / Everyday Shopper Tip
    claimed_cat = (product.claimed_category or "").lower()
    p_name = product.product_name.lower()
    
    if any(k in claimed_cat or k in p_name for k in ["snack", "savoury", "namak", "bhujia", "chips", "cracker", "para"]):
        swap = "💡 <b>Smart Swap:</b> Try roasted makhana (foxnuts), roasted chana (chickpeas), or baked unpolished millet chips seasoned with rock salt. They offer the same satisfying crunch with 5x more fiber and zero palm oil!"
    elif any(k in claimed_cat or k in p_name for k in ["biscuit", "cookie", "digestive", "rusk"]):
        swap = "💡 <b>Smart Swap:</b> Look for 100% whole grain biscuits baked with real butter or cold-pressed oils without palm oil, or pair evening tea with fresh whole fruit and a handful of almonds."
    elif any(k in claimed_cat or k in p_name for k in ["bar", "cereal", "drink", "shake", "health"]):
        swap = "💡 <b>Smart Swap:</b> Choose whole dates, homemade trail mix, or raw nut-and-seed bars with zero artificial syrups or synthetic additives."
    else:
        swap = "💡 <b>Everyday Shopper Rule:</b> Always look at the first 3 ingredients on the back. If you spot Maida, Palm Oil, or Sugar as #1 or #2, the front label is heavily exaggerating its health value."
        
    return {
        "headline": headline,
        "headline_color": headline_color,
        "bottom_line": bottom_line,
        "marketing_truths": marketing_truths,
        "ingredients_plain": ingredients_plain,
        "chemicals_plain": chemicals_plain,
        "health_cautions": health_cautions,
        "smart_swap": swap
    }

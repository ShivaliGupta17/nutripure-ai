"""
Extraction & Normalization Engine for NutriPure AI.
Parses raw ingredients text and packaging images into structured Pydantic models.
Authoritative INS code detection across standard, bracketed, and Indian FMCG formats.
"""

import os
import re
import json
from typing import List, Dict, Tuple, Optional
from src.schemas import ExtractedIngredient, NutritionalFacts, ProductInput


def load_chemical_registry(db_path: str = "data/chemical_db/ins_codes.json") -> Dict:
    """Loads the INS codes and disguised sugar dictionary."""
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"additives": [], "disguised_sugars": []}


def extract_ins_codes(text: str) -> List[str]:
    """
    Finds all INS and E-number codes in text across all packaging declaration styles:
    - Explicit prefix: 'INS 503(ii)', 'INS 150d', 'E635', 'INS-471'
    - Functional category bracketed numbers: 'Thickeners (508 & 412)', 'Acidity regulators (501(i) & 500(ii))',
      'Flavour enhancer (635)', 'Colour (150d)', 'Humectant (451(ii))', 'Emulsifiers [471, 322]'
    - Direct 3-4 digit numbers inside parentheses/brackets: '(508)', '[500(ii)]', '(635)'
    """
    normalized: List[str] = []

    def _add_code(raw_num: str):
        cleaned = raw_num.strip()
        # Filter out 4-digit years like 2024, 2026 or small numbers
        if re.match(r'^(?:19\d\d|20\d\d)$', cleaned):
            return
        code = f"INS {cleaned}"
        if code not in normalized:
            normalized.append(code)

    # 1. Explicit INS or E prefix (case-insensitive)
    explicit_pat = r'\b(?:INS|E)[-\s]?([0-9]{3,4}[a-zA-Z]?(?:\([a-zA-Z0-9ivxIVX]+\))?)'
    for m in re.finditer(explicit_pat, text, re.IGNORECASE):
        _add_code(m.group(1))

    # 2. Additive functional class words followed by parentheses/brackets
    class_kw = (
        r'(?:thickener|thickeners|acidity regulator|acidity regulators|humectant|humectants|'
        r'flavour enhancer|flavour enhancers|flavor enhancer|flavor enhancers|colour|colours|color|colors|'
        r'raising agent|raising agents|emulsifier|emulsifiers|stabilizer|stabilizers|stabiliser|stabilisers|'
        r'preservative|preservatives|antioxidant|antioxidants|glazing agent|glazing agents|'
        r'sweetener|sweeteners|anti-caking agent|anti-caking agents|anticaking agent|firming agent|gelling agent|carrier)'
    )
    # Match balanced / nested parentheses up to 1 level deep: e.g. (501(i) & 500(ii))
    cat_pattern = rf'\b{class_kw}\s*[\(\[]((?:[^()\[\]]+|\([^()]*\)|\[[^\[\]]*\])*)[\)\]]'
    for match in re.finditer(cat_pattern, text, re.IGNORECASE):
        inside = match.group(1)
        for nm in re.finditer(r'\b([1-9][0-9]{2,3}[a-zA-Z]?(?:\([a-zA-Z0-9ivxIVX]+\))?)', inside):
            _add_code(nm.group(1))

    # 3. Direct numbers inside parentheses or brackets: (635), [503(ii)], (150d)
    paren_pattern = r'[\(\[]\s*([1-9][0-9]{2,3}[a-zA-Z]?(?:\([a-zA-Z0-9ivxIVX]+\))?)\s*[\)\]]'
    for match in re.finditer(paren_pattern, text):
        _add_code(match.group(1))

    return normalized


def parse_ingredient_list(raw_text: str) -> List[ExtractedIngredient]:
    """
    Parses complex packaging ingredients text into structured ExtractedIngredient instances.
    Handles nested brackets, compound additives, QUID percentages, and INS code detection.
    """
    # Strip terminal regulatory notices, allergens, or advisory banners
    cleaned_text = re.split(
        r'~|(?:\bCONTAINS PERMITTED\b)|(?:\bMAY CONTAIN\b)|(?:\bALLERGEN ADVICE\b)',
        raw_text,
        flags=re.IGNORECASE
    )[0].strip()

    # Balanced delimiter tokenization: split on , ; and ' and ' outside (), [], and {}
    raw_tokens = []
    current = []
    depth = 0
    n = len(cleaned_text)
    i = 0

    while i < n:
        ch = cleaned_text[i]
        if ch in '([{':
            depth += 1
            current.append(ch)
            i += 1
        elif ch in ')]}':
            depth = max(0, depth - 1)
            current.append(ch)
            i += 1
        elif (ch in ',;' or (ch == '.' and depth == 0)) and depth == 0:
            tok = ''.join(current).strip()
            if tok:
                raw_tokens.append(tok)
            current = []
            i += 1
        elif depth == 0:
            # Check for conjunction ' and ' or ' & ' at depth 0 separating items
            m_and = re.match(r'^\s+(?:and|&)\s+', cleaned_text[i:], re.IGNORECASE)
            if m_and:
                snippet = cleaned_text[max(0, i-15):min(n, i+35)].lower()
                protected = ['spices and condiments', 'herbs and spices', 'spices and herbs', 'cookies and cream', 'salt and vinegar']
                if not any(p in snippet for p in protected):
                    tok = ''.join(current).strip()
                    if tok:
                        raw_tokens.append(tok)
                    current = []
                    i += m_and.end()
                    continue
            current.append(ch)
            i += 1
        else:
            current.append(ch)
            i += 1

    if current:
        tok = ''.join(current).strip()
        if tok:
            raw_tokens.append(tok)

    # Secondary split on section headers (e.g. "Masala TASTEMAKER*:") and compound additives ("and Humectant")
    split_tokens = []
    for tok in raw_tokens:
        tok = tok.strip().strip('.,;')
        if not tok:
            continue

        # Split on section headings preceded by periods or colons
        sec_parts = re.split(r'(?<=\))\s*\.\s*(?=[A-Z])|(?<=[a-z0-9])\.\s+(?=[A-Z])', tok)
        for part in sec_parts:
            part = part.strip()
            if not part:
                continue

            # Split compound additives joined by 'and' or '&' (e.g. "Acidity regulators (...) and Humectant (...)")
            compound_parts = re.split(
                r'\s+(?:and|&)\s+(?=(?:thickener|acidity regulator|humectant|flavour enhancer|flavor enhancer|colour|color|raising agent|emulsifier|stabilizer|preservative|antioxidant|mineral)\b)',
                part,
                flags=re.IGNORECASE
            )
            for cp in compound_parts:
                cp = cp.strip()
                if cp:
                    split_tokens.append(cp)

    parsed_ingredients = []
    for token in split_tokens:
        # Extract percentage if present (e.g., "Refined Wheat Flour (Maida) 62%", "Red chilli powder (3%)")
        pct_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%', token)
        percentage = float(pct_match.group(1)) if pct_match else None

        # Clean ingredient name: remove percentages and any resulting empty () [] {}
        clean_name = re.sub(r'[\(\[\{]\s*[0-9]+(?:\.[0-9]+)?\s*%\s*[\)\]\}]', '', token)
        clean_name = re.sub(r'([0-9]+(?:\.[0-9]+)?)\s*%', '', clean_name)
        clean_name = re.sub(r'[\(\[\{]\s*[\)\]\}]', '', clean_name)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip(' :,.-')

        # Check for INS codes within this specific token
        ins_codes = extract_ins_codes(token)
        is_additive = len(ins_codes) > 0 or any(keyword in token.lower() for keyword in [
            'preservative', 'emulsifier', 'raising agent', 'colour', 'color', 
            'flavour', 'flavor', 'sweetener', 'stabilizer', 'thickener', 'acidity regulator',
            'humectant', 'anti-caking', 'mineral'
        ])

        ins_code_str = ", ".join(ins_codes) if ins_codes else None

        parsed_ingredients.append(
            ExtractedIngredient(
                name=clean_name if clean_name else token,
                percentage=percentage,
                is_additive=is_additive,
                ins_code=ins_code_str,
                raw_text=token
            )
        )

    return parsed_ingredients


def detect_disguised_sugars(ingredients_text: str, registry: Optional[Dict] = None) -> List[str]:
    """Identifies industrial high-glycemic disguised sugars in the ingredients list."""
    if registry is None:
        registry = load_chemical_registry()
        
    detected = []
    lower_text = ingredients_text.lower()
    
    for item in registry.get("disguised_sugars", []):
        sugar_name = item.get("name", "")
        if sugar_name.lower() in lower_text:
            if sugar_name not in detected:
                detected.append(sugar_name)
        # Check aliases
        for alias in item.get("aliases", []):
            if alias.lower() in lower_text:
                if sugar_name not in detected:
                    detected.append(sugar_name)
                    
    return detected


def build_product_input(
    id: str,
    product_name: str,
    brand: str,
    claimed_category: str,
    front_claims: List[str],
    ingredients_text: str,
    nutritional_facts: Optional[Dict] = None
) -> ProductInput:
    """
    Constructs a validated ProductInput object.
    Automatically parses ingredients, extracts percentages, and registers INS codes.
    """
    ingredients = parse_ingredient_list(ingredients_text)
    detected_ins = extract_ins_codes(ingredients_text)
    
    nutri_obj = NutritionalFacts(**(nutritional_facts or {}))
    
    return ProductInput(
        id=id,
        product_name=product_name,
        brand=brand,
        claimed_category=claimed_category,
        front_claims=front_claims,
        raw_ingredients_text=ingredients_text,
        ingredients=ingredients,
        nutritional_facts=nutri_obj,
        declared_ins_codes=detected_ins
    )


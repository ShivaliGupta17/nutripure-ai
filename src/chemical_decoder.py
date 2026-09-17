"""
Chemical & Additive Decoder for NutriPure AI.
Resolves INS and E-number codes to standardized chemical names,
toxicity profiles, health hazards, and contraindications.
"""

import json
import os
from typing import List, Dict, Optional
from src.schemas import DecodedAdditive, ProductInput


class ChemicalDecoder:
    """Decodes food additive numbers against the curated chemical registry."""
    
    def __init__(self, db_path: str = "data/chemical_db/ins_codes.json"):
        self.db_path = db_path
        self.additives_map: Dict[str, Dict] = {}
        self.disguised_sugars: List[Dict] = []
        self._load_registry()
        
    def _load_registry(self):
        if not os.path.exists(self.db_path):
            return
            
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for item in data.get("additives", []):
            code = item["code"].upper()
            self.additives_map[code] = item
            # Also map aliases
            for alias in item.get("aliases", []):
                self.additives_map[alias.upper()] = item
                
        self.disguised_sugars = data.get("disguised_sugars", [])

    def lookup_code(self, code: str) -> Optional[DecodedAdditive]:
        """Looks up a single INS or E-code and returns a DecodedAdditive schema."""
        clean_code = code.strip().upper()
        
        # Try direct match
        item = self.additives_map.get(clean_code)
        
        # Try without 'INS' or 'E' prefix
        if not item:
            stripped = clean_code.replace("INS", "").replace("E", "").strip()
            item = self.additives_map.get(stripped) or self.additives_map.get(f"INS {stripped}")
            
        if item:
            return DecodedAdditive(
                code=item["code"],
                chemical_name=item["name"],
                category=item["category"],
                risk_level=item["risk_level"],
                description=item["description"],
                health_warnings=item.get("health_warnings", []),
                contraindications=item.get("contraindications", []),
                is_disguised_sugar=item.get("is_disguised_sugar", False)
            )
            
        # Fallback for unrecognized codes
        return DecodedAdditive(
            code=code,
            chemical_name=f"Food Additive {code}",
            category="Synthetic Additive",
            risk_level="Moderate",
            description="Additive identified by International Numbering System code.",
            health_warnings=["Additive profile pending live database query."],
            contraindications=[]
        )

    def decode_all(self, product: ProductInput) -> List[DecodedAdditive]:
        """Decodes all INS codes identified in a ProductInput object."""
        decoded = []
        seen = set()
        
        for code in product.declared_ins_codes:
            if code not in seen:
                seen.add(code)
                decoded.append(self.lookup_code(code))
                
        # Also check ingredient names directly for additive names (e.g., Carrageenan, MSG)
        for ing in product.ingredients:
            if ing.ins_code:
                for c in ing.ins_code.split(","):
                    c = c.strip()
                    if c and c not in seen:
                        seen.add(c)
                        decoded.append(self.lookup_code(c))
                
        return decoded

"""
Multimodal Vision Extractor for NutriPure AI.
Supports Groq Vision (Qwen 3.8 27B) and Google Gemini Vision
to read food packaging photos, extracting product names, front marketing claims,
and raw ingredients text into validated Pydantic models.
"""

import os
import io
import json
import re
import base64
from typing import Optional, Dict, Any, List
from PIL import Image
from dotenv import load_dotenv

from src.schemas import ProductInput, NutritionalFacts
from src.extractor import build_product_input

load_dotenv()


class VisionLabelExtractor:
    """Extracts structured food product data from packaging photos using Groq or Gemini Vision."""

    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Support Streamlit Community Cloud Secrets (st.secrets)
        try:
            import streamlit as st
            if not self.groq_api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                self.groq_api_key = st.secrets["GROQ_API_KEY"]
            if not self.gemini_api_key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                self.gemini_api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

        # If user explicitly passed an api_key
        if api_key:
            if api_key.startswith("gsk_"):
                self.groq_api_key = api_key
            else:
                self.gemini_api_key = api_key

        self.groq_client = None
        self.gemini_client = None
        
        # Initialize Groq if key available
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize Groq client: {e}")

        # Initialize Gemini if key available
        if self.gemini_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize Gemini GenAI client: {e}")

    def is_available(self) -> bool:
        """Returns True if either Groq or Gemini Vision is configured."""
        return self.groq_client is not None or self.gemini_client is not None

    def active_provider_name(self) -> str:
        """Returns the active provider name for UI feedback."""
        if self.groq_client:
            return "Groq Vision (Qwen 3.8-27B)"
        if self.gemini_client:
            return "Google Gemini Vision"
        return "None (API Key Required)"

    def extract_from_image(self, image: Image.Image) -> ProductInput:
        """Convenience method for a single packaging photo."""
        return self.extract_from_images([image])

    def extract_from_images(
        self,
        images: List[Image.Image],
        image_labels: Optional[List[str]] = None
    ) -> ProductInput:
        """
        Sends one or multiple packaging images (e.g. Front & Back) to Vision AI
        and parses extracted fields into a unified ProductInput schema.
        """
        if not self.is_available():
            raise ValueError(
                "No Vision API key configured. Please ensure GROQ_API_KEY or GEMINI_API_KEY is in .env."
            )

        if not images:
            raise ValueError("No images provided for vision extraction.")

        # Filter out any None
        valid_images = [img for img in images if img is not None]
        if not valid_images:
            raise ValueError("All provided images were empty.")

        # Build multi-image prompt
        if len(valid_images) > 1:
            context_note = (
                "You are provided with multiple packaging photos of the same food product "
                "(for example, Front-of-Pack showing brand, product name, and marketing claims; "
                "and Back-of-Pack showing ingredients declaration, QUID percentages, and nutrition facts). "
                "Cross-reference and synthesize ALL text across all provided images into one consolidated JSON."
            )
        else:
            context_note = "Analyze this food packaging image and extract the food information into valid JSON."

        prompt = f"""
You are an expert food safety auditor for NutriPure AI.
{context_note}

Extract the following details into valid JSON format:
{{
  "product_name": "Full product name as printed",
  "brand": "Manufacturer or brand name",
  "claimed_category": "Product category like Biscuits, Breakfast Cereal, Beverage, Snack, Instant Noodles",
  "front_claims": ["List of marketing claims on packaging like '100% Atta', 'Zero Sugar', 'High Fiber', 'No Preservatives'"],
  "ingredients_text": "Exact full ingredients text as printed on the packaging, including percentages and INS/E-numbers",
  "nutritional_facts": {{
    "serving_size": "Serving size e.g. 'Per 100g' or '30g'",
    "energy_kcal": 0.0,
    "protein_g": 0.0,
    "carbohydrates_g": 0.0,
    "total_sugars_g": 0.0,
    "added_sugars_g": 0.0,
    "dietary_fiber_g": 0.0,
    "total_fat_g": 0.0,
    "saturated_fat_g": 0.0,
    "trans_fat_g": 0.0,
    "cholesterol_mg": 0.0,
    "sodium_mg": 0.0
  }}
}}

CRITICAL EXTRACTION GUIDELINES:
1. Nutrition Information Table: Carefully locate and extract the printed nutrition table on the packaging. Prefer values per 100g (or per serve if that is what is printed). Convert entries like '< 0.1g' to 0.1, and 'NIL' or '-' to 0.0. If a nutrient is not present in the table, set to null. Do NOT skip the nutrition table!
2. Ingredients Declaration: Extract the full ingredients list verbatim without omitting any parenthesized additives (e.g. INS 500iii, INS 635) or percentages.
3. Marketing Claims: Extract all prominent front-of-pack claims and health banners.

Return ONLY valid JSON. Do not include markdown commentary.
"""

        raw_text = ""
        # 1. Try Groq Vision first if available
        if self.groq_client:
            try:
                groq_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
                for img in valid_images:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=90)
                    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    groq_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    })

                try:
                    response = self.groq_client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[{"role": "user", "content": groq_content}],
                        temperature=0.1,
                        max_tokens=650,
                        response_format={"type": "json_object"}
                    )
                    raw_text = response.choices[0].message.content.strip()
                except Exception as first_err:
                    if "429" in str(first_err) or "tokens" in str(first_err).lower():
                        print(f"[WARN] Groq rate limit encountered: {first_err}. Retrying with max_tokens=480...")
                        response = self.groq_client.chat.completions.create(
                            model="qwen/qwen3.8-27b",
                            messages=[{"role": "user", "content": groq_content}],
                            temperature=0.1,
                            max_tokens=480,
                            response_format={"type": "json_object"}
                        )
                        raw_text = response.choices[0].message.content.strip()
                    else:
                        raise first_err
            except Exception as e:
                err_str = str(e)
                print(f"[WARN] Groq Vision call failed: {err_str}. Trying fallback if available.")
                if not self.gemini_client:
                    if "429" in err_str or "rate_limit" in err_str:
                        raise RuntimeError("Groq Vision free-tier rate limit (1000 tokens/min) reached. Please wait 15 seconds and click extract again.")
                    raise RuntimeError(f"Groq Vision extraction failed: {err_str}")

        # 2. Try Gemini if Groq wasn't used or failed
        if not raw_text and self.gemini_client:
            try:
                gemini_contents = []
                for img in valid_images:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    gemini_contents.append(img)
                gemini_contents.append(prompt)

                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=gemini_contents
                )
                raw_text = response.text.strip()
            except Exception as e:
                raise RuntimeError(f"Gemini Vision extraction failed: {str(e)}")

        if not raw_text:
            raise RuntimeError("Vision model returned an empty response.")

        # Clean JSON markdown fences
        cleaned_json = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
        cleaned_json = re.sub(r'\s*```$', '', cleaned_json, flags=re.MULTILINE).strip()

        # Parse JSON
        try:
            data = json.loads(cleaned_json)
        except Exception:
            match = re.search(r'(\{.*\})', cleaned_json, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                raise ValueError(f"Could not parse valid JSON from vision response:\n{cleaned_json}")

        # Sanitize front_claims into list of strings
        claims = data.get("front_claims", [])
        if isinstance(claims, str):
            claims = [c.strip() for c in claims.split(",") if c.strip()]
        elif isinstance(claims, list):
            clean_claims = []
            for c in claims:
                if isinstance(c, str):
                    clean_claims.append(c.strip())
                elif isinstance(c, dict):
                    clean_claims.append(str(c))
            claims = clean_claims

        return build_product_input(
            id="scanned_packaging_label",
            product_name=data.get("product_name", "Scanned Food Product"),
            brand=data.get("brand", "Unknown Brand"),
            claimed_category=data.get("claimed_category", "Packaged Food"),
            front_claims=claims,
            ingredients_text=data.get("ingredients_text", ""),
            nutritional_facts=data.get("nutritional_facts")
        )

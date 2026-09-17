"""
Generates clean sample packaging label images for instant photo upload testing:
- Front of Pack (Brand, Product Name, Marketing Claims)
- Back of Pack (Ingredients Declaration, QUID %, INS Codes, Nutrition Facts)
"""

import os
from PIL import Image, ImageDraw


def create_front_pack(output_path: str, title: str, brand: str, claims: list):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 700, 450
    image = Image.new("RGB", (width, height), color="#FFFDF7")
    draw = ImageDraw.Draw(image)

    # Borders
    draw.rectangle([(16, 16), (width - 16, height - 16)], outline="#D97706", width=4)
    draw.rectangle([(24, 24), (width - 24, height - 24)], outline="#B45309", width=2)

    # Top Brand Bar
    draw.rectangle([(26, 26), (width - 26, 90)], fill="#B45309")
    draw.text((45, 45), f"★ {brand.upper()} ★", fill="#FFFFFF")

    # Title Card
    draw.text((45, 120), title, fill="#78350F")

    # Front Marketing Claims Badges
    y = 190
    for claim in claims:
        draw.rectangle([(45, y), (width - 45, y + 45)], fill="#FEF3C7", outline="#F59E0B", width=2)
        draw.text((65, y + 12), f"✔ {claim}", fill="#92400E")
        y += 60

    # Net weight & footer
    draw.text((45, height - 60), "NET WT. 300g | 100% VEGETARIAN FOOD PRODUCT", fill="#64748B")

    image.save(output_path, "PNG")
    print(f"[OK] Generated front-of-pack image: {output_path}")


def create_back_pack(output_path: str, title: str, brand: str, ingredients: str, nutrition: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 700, 520
    image = Image.new("RGB", (width, height), color="#F8FAFC")
    draw = ImageDraw.Draw(image)

    # Borders
    draw.rectangle([(16, 16), (width - 16, height - 16)], outline="#475569", width=3)

    # Header
    draw.text((35, 30), f"{brand} — {title} (BACK OF PACK DECLARATION)", fill="#0F172A")
    draw.line([(35, 60), (width - 35, 60)], fill="#94A3B8", width=2)

    # Ingredients section
    draw.text((35, 80), "INGREDIENTS:", fill="#1E293B")
    words = ingredients.split()
    lines, curr = [], []
    for w in words:
        curr.append(w)
        if len(" ".join(curr)) > 68:
            lines.append(" ".join(curr))
            curr = []
    if curr:
        lines.append(" ".join(curr))

    y = 110
    for l in lines:
        draw.text((40, y), l, fill="#334155")
        y += 24

    # Nutrition section
    y += 20
    draw.rectangle([(35, y), (width - 35, y + 160)], outline="#64748B", width=2)
    draw.text((45, y + 12), "NUTRITIONAL FACTS (Per 100g Approx.)", fill="#0F172A")

    y_nutri = y + 42
    for nl in nutrition.split("\n"):
        draw.text((50, y_nutri), nl, fill="#475569")
        y_nutri += 22

    # Allergy Advice
    draw.text((35, height - 55), "ALLERGEN ADVICE: Contains Wheat (Gluten), Milk and Soy derivatives.", fill="#DC2626")

    image.save(output_path, "PNG")
    print(f"[OK] Generated back-of-pack image: {output_path}")


if __name__ == "__main__":
    brand = "VitaWheat Foods"
    title = "100% Atta Digestives Biscuits"
    claims = ["100% Whole Wheat Atta", "Goodness of High Fiber", "Zero Trans Fat"]
    ingredients = "Refined Wheat Flour (Maida) 62%, Whole Wheat Flour (Atta) 24%, Edible Vegetable Oil (Refined Palm Oil), Sugar, Invert Sugar Syrup, Raising Agents [INS 503(ii), INS 500(ii)], Emulsifier [INS 471, INS 322], Iodised Salt, Artificial Flavouring (Milk, Vanilla)."
    nutrition = "Energy: 478 kcal | Protein: 6.8g | Carbohydrates: 68.0g\nTotal Sugars: 24.5g | Added Sugars: 22.0g | Total Fat: 20.0g\nSaturated Fat: 10.2g | Trans Fat: 0.05g | Sodium: 380mg"

    create_front_pack("data/sample_products/sample_vitawheat_front.png", title, brand, claims)
    create_back_pack("data/sample_products/sample_vitawheat_back.png", title, brand, ingredients, nutrition)


"""
NutriPure AI - Streamlit Interactive Web Application.
Modern, sleek, high-tech AI dashboard for auditing packaged food,
detecting deceptive marketing claims, decoding E-numbers, and personalized HITL gating.
"""

import os
import re
import json
from typing import Optional, List, Dict, Any
import streamlit as st
from PIL import Image

def md_to_html(text: str) -> str:
    """Converts markdown formatting to HTML tags for safe rendering inside raw HTML div cards."""
    if not text:
        return ""
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    # Italic: *text* or _text_
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    return text


from src.schemas import (
    ProductInput,
    NutritionalFacts,
    ClaimAdjudication,
    HITLAdjudicationPayload,
)
from src.extractor import build_product_input, detect_disguised_sugars
from src.chemical_decoder import ChemicalDecoder
from src.rag_engine import RegulatoryRAG
from src.mcp_tools import MCPToolRegistry
from src.hitl import NutriAuditHITLGraph, UserHealthProfile, PersonalizedSafetyAuditor
from src.graph import NutriAuditGraph
from src.vision_extractor import VisionLabelExtractor
from src.nutrition_hazards import evaluate_nutritional_hazards, generate_nova_explanation
from src.plain_summary import generate_plain_english_summary


# Page Configuration
st.set_page_config(
    page_title="NutriPure AI | Know What’s Really Inside Your Food",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Tech Modern CSS Styling (Adaptive for Dark & Light Themes)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hero Gradient Header */
    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #10B981 0%, #06B6D4 50%, #6366F1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        display: inline-block;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        font-weight: 400;
        margin-bottom: 1.2rem;
    }

    /* Feature Pills */
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        margin-right: 8px;
        margin-bottom: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(8px);
        color: #E2E8F0;
    }

    /* Glassmorphism Product Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    /* Marketing Claim Tags */
    .claim-tag {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 3px 6px 3px 0;
    }

    /* Violation Cards */
    .violation-card-dark {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-left: 5px solid #EF4444;
        padding: 1.1rem;
        margin-bottom: 0.9rem;
        border-radius: 8px;
        color: #F8FAFC;
    }

    .clean-card-dark {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-left: 5px solid #10B981;
        padding: 1.1rem;
        margin-bottom: 0.9rem;
        border-radius: 8px;
        color: #F8FAFC;
    }

    .alert-card-dark {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-radius: 8px;
        color: #FEF3C7;
    }

    /* Hazard Badges */
    .badge-high {
        background: linear-gradient(135deg, #DC2626, #EF4444);
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-mod {
        background: linear-gradient(135deg, #D97706, #F59E0B);
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-safe {
        background: linear-gradient(135deg, #059669, #10B981);
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Sleek Action Button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 18px rgba(16, 185, 129, 0.4) !important;
        transition: all 0.25s ease-in-out !important;
    }

    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(16, 185, 129, 0.6) !important;
    }

    /* Pulse Status Indicator */
    .pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 1.6s infinite;
        margin-right: 6px;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_cached_systems():
    """Initializes backend systems once and caches in memory."""
    rag = RegulatoryRAG()
    rag.build_index()
    decoder = ChemicalDecoder()
    mcp = MCPToolRegistry()
    graph = NutriAuditGraph(rag_engine=rag, chemical_decoder=decoder, mcp_registry=mcp)
    hitl = NutriAuditHITLGraph(rag_engine=rag, chemical_decoder=decoder, mcp_registry=mcp)
    return rag, decoder, mcp, graph, hitl


rag_engine, chemical_decoder, mcp_registry, audit_graph, hitl_system = load_cached_systems()
vision_extractor = VisionLabelExtractor()


def format_nutrition_table_html(nutri: Optional[NutritionalFacts]) -> str:
    """Renders a clean, styled HTML table of nutritional facts per 100g/serving."""
    if not nutri:
        return '<div style="color:#94A3B8; text-align:center; padding:18px;">No nutrition table detected</div>'
    
    rows = []
    if nutri.energy_kcal is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08);"><td style="padding:4px 0;"><b>Energy</b></td><td style="text-align:right; padding:4px 0;"><b>{nutri.energy_kcal:.1f} kcal</b></td></tr>')
    if nutri.protein_g is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08);"><td style="padding:4px 0;">Protein</td><td style="text-align:right; padding:4px 0;">{nutri.protein_g:.1f} g</td></tr>')
    if nutri.carbohydrates_g is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08);"><td style="padding:4px 0;">Carbohydrates</td><td style="text-align:right; padding:4px 0;">{nutri.carbohydrates_g:.1f} g</td></tr>')
    if nutri.total_sugars_g is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08); color:#FCA5A5;"><td style="padding:4px 0;">&nbsp;&nbsp;&#8627; Total Sugars</td><td style="text-align:right; padding:4px 0;"><b>{nutri.total_sugars_g:.1f} g</b></td></tr>')
    if nutri.added_sugars_g is not None and nutri.added_sugars_g > 0:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08); color:#EF4444;"><td style="padding:4px 0;">&nbsp;&nbsp;&#8627; Added Sugars</td><td style="text-align:right; padding:4px 0;"><b>{nutri.added_sugars_g:.1f} g</b></td></tr>')
    if nutri.total_fat_g is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08);"><td style="padding:4px 0;">Total Fat</td><td style="text-align:right; padding:4px 0;">{nutri.total_fat_g:.1f} g</td></tr>')
    if nutri.saturated_fat_g is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08); color:#FCD34D;"><td style="padding:4px 0;">&nbsp;&nbsp;&#8627; Saturated Fat</td><td style="text-align:right; padding:4px 0;">{nutri.saturated_fat_g:.1f} g</td></tr>')
    if nutri.trans_fat_g is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08);"><td style="padding:4px 0;">&nbsp;&nbsp;&#8627; Trans Fat</td><td style="text-align:right; padding:4px 0;">{nutri.trans_fat_g:.2f} g</td></tr>')
    if nutri.cholesterol_mg is not None:
        rows.append(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.08);"><td style="padding:4px 0;">Cholesterol</td><td style="text-align:right; padding:4px 0;">{nutri.cholesterol_mg:.1f} mg</td></tr>')
    if nutri.sodium_mg is not None:
        rows.append(f'<tr><td style="padding:4px 0;">Sodium</td><td style="text-align:right; padding:4px 0;">{nutri.sodium_mg:.1f} mg</td></tr>')

    if not rows:
        return '<div style="color:#94A3B8; text-align:center; padding:18px;">No nutritional values found</div>'
    
    return '<table style="width:100%; border-collapse:collapse;">' + ''.join(rows) + '</table>'


# ---------------------------------------------------------
# Persistent Upload Caching & Session Reset Utilities
# ---------------------------------------------------------
UPLOAD_CACHE_DIR = os.path.join("data", "uploaded_cache")
os.makedirs(UPLOAD_CACHE_DIR, exist_ok=True)


def save_uploaded_cache(slot: str, uploaded_file) -> Optional[Image.Image]:
    """Saves uploaded image bytes to disk cache and returns loaded PIL Image."""
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.load()
        path = os.path.join(UPLOAD_CACHE_DIR, f"{slot}.png")
        meta_path = os.path.join(UPLOAD_CACHE_DIR, f"{slot}_meta.json")
        img.save(path, format="PNG")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "name": getattr(uploaded_file, "name", f"{slot}.png"),
                "size": getattr(uploaded_file, "size", 0)
            }, f)
        return img
    except Exception as e:
        st.error(f"Error caching {slot} photo: {e}")
        return None


def get_cached_image(slot: str) -> Optional[Image.Image]:
    """Retrieves cached image from disk if available."""
    path = os.path.join(UPLOAD_CACHE_DIR, f"{slot}.png")
    if os.path.exists(path):
        try:
            img = Image.open(path)
            img.load()
            return img
        except Exception:
            return None
    return None


def get_cached_meta(slot: str) -> Dict[str, Any]:
    """Retrieves metadata (filename, etc.) for cached image."""
    meta_path = os.path.join(UPLOAD_CACHE_DIR, f"{slot}_meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def clear_upload_cache(slot: Optional[str] = None):
    """Clears cached images and metadata from disk."""
    slots = [slot] if slot else ["front", "back"]
    for s in slots:
        for ext in [".png", "_meta.json"]:
            p = os.path.join(UPLOAD_CACHE_DIR, f"{s}{ext}")
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
    if not slot:
        p_ext = os.path.join(UPLOAD_CACHE_DIR, "last_extracted.json")
        if os.path.exists(p_ext):
            try:
                os.remove(p_ext)
            except Exception:
                pass


def reset_audit_session():
    """Completely resets the active audit session, clearing all uploaded photos, extracted models, and reports."""
    clear_upload_cache()
    keys_to_clear = [
        "active_product", "active_source", "photo_extracted_product",
        "front_image_data", "back_image_data", "front_uploader_active", "back_uploader_active",
        "hitl_interrupted", "hitl_payload", "hitl_state_values", "hitl_product_id", "hitl_thread_id",
        "audit_report", "audit_product_id", "front_photo_uploader", "back_photo_uploader"
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    try:
        st.query_params.clear()
    except Exception:
        pass


# ---------------------------------------------------------
# Sidebar: Knowledge & Tool Layer and Architecture Specs
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌿 NutriPure AI")
    st.markdown('<span class="pulse-dot"></span> **System Status:** Active & Ready', unsafe_allow_html=True)
    st.caption("Autonomous Food Truth & Deceptive Claim Auditor with LangGraph Agentic Intelligence.")
    st.markdown("---")
    
    st.markdown("### 🧑‍⚖️ Interactive HITL Checkpoint")
    st.info(
        "**True In-Stream Human-in-the-Loop:** When you trigger an audit, the AI agent pauses execution at a compliance gate. "
        "You can review flagged claims, configure product-specific health alerts, and append official nutritionist directives before final certification."
    )
    st.markdown("---")
    
    st.markdown("### 🏛️ Knowledge & Tool Layer")
    st.markdown(f"• **Vision AI:** `{vision_extractor.active_provider_name()}`")
    st.markdown("• **Vector DB (RAG):** `ChromaDB (670 Chunks: FSSAI Gazette & WHO)`")
    st.markdown("• **Chemical Registry:** `80+ INS / E-Number Additives DB`")
    st.markdown("• **MCP Tool Layer:** `Live FSSAI Alerts & EFSA Registry (MCP Tool Schema)`")
    st.markdown("• **State Engine:** `LangGraph (SqliteSaver Checkpointed)`")
    st.markdown("• **HITL Mode:** `In-Stream Interrupt Gate`")
    st.markdown("• **Clinical Hazard Engine:** `WHO REPLACE & ICMR-NIN 2024`")
    
    st.markdown("---")
    st.markdown("### 🔄 Session Controls")
    if st.button("🧹 Clear All & Start Fresh", key="sidebar_reset_btn", use_container_width=True, help="Wipes all uploaded photos, active audit targets, and paused HITL gates"):
        reset_audit_session()
        st.rerun()


# ---------------------------------------------------------
# Main Header with Top-Right System Architecture Popover
# ---------------------------------------------------------
col_head1, col_head2 = st.columns([3.6, 1.5])

with col_head1:
    st.markdown('<div class="hero-title">NutriPure AI 🌿</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Know What’s Really Inside Your Food • Autonomous Food Truth & Deceptive Claim Auditor</div>', unsafe_allow_html=True)

with col_head2:
    st.write("")
    with st.popover("⚡ System Architecture", use_container_width=True):
        st.markdown("#### 🏗️ AI System Architecture")
        st.caption("Under the hood: Multimodal Vision AI + LangGraph Orchestration + ChromaDB Regulatory RAG.")
        
        st.markdown(f"""
        <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:10px 12px; margin-bottom:8px;">
            <b style="color:#10B981; font-size:0.88rem;">📸 Multimodal Vision OCR</b>
            <div style="font-size:0.8rem; color:#CBD5E1; margin-top:4px; line-height:1.4;">
                • Engine: {vision_extractor.active_provider_name()}<br/>
                • Dual-Image Fusion: Front + Back Labels<br/>
                • Automatic QUID % & INS Code Parsing
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.3); border-radius:8px; padding:10px 12px; margin-bottom:8px;">
            <b style="color:#38BDF8; font-size:0.88rem;">⚡ Agentic Graph Orchestration</b>
            <div style="font-size:0.8rem; color:#CBD5E1; margin-top:4px; line-height:1.4;">
                • Framework: LangGraph StateGraph (5 Nodes)<br/>
                • Persistence: SQLiteSaver Thread Checkpointing<br/>
                • HITL: True In-Stream Compliance Gate
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background:rgba(168,85,247,0.08); border:1px solid rgba(168,85,247,0.3); border-radius:8px; padding:10px 12px; margin-bottom:8px;">
            <b style="color:#A855F7; font-size:0.88rem;">📚 Statutory RAG & MCP Layer</b>
            <div style="font-size:0.8rem; color:#CBD5E1; margin-top:4px; line-height:1.4;">
                • Vector DB: ChromaDB (670 Chunks)<br/>
                • Standards: FSSAI Gazette, WHO, ICMR-NIN<br/>
                • MCP Schema: Live Alerts & Recall Registry
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# Load Benchmark Dataset
dataset_path = os.path.join("data", "sample_products", "test_products.json")
with open(dataset_path, "r", encoding="utf-8") as f:
    benchmark_products = json.load(f)

# Initialize Session State for Active Audit Target
if "active_product" not in st.session_state:
    first_raw = benchmark_products[0]
    st.session_state["active_product"] = build_product_input(
        id=first_raw["id"],
        product_name=first_raw["product_name"],
        brand=first_raw["brand"],
        claimed_category=first_raw["claimed_category"],
        front_claims=first_raw["front_claims"],
        ingredients_text=first_raw["ingredients_text"],
        nutritional_facts=first_raw.get("nutritional_facts_per_100g")
    )
    st.session_state["active_source"] = f"Benchmark: {first_raw['product_name']}"


# Restore cached extracted product if available
ext_cache_file = os.path.join(UPLOAD_CACHE_DIR, "last_extracted.json")
if "photo_extracted_product" not in st.session_state and os.path.exists(ext_cache_file):
    try:
        with open(ext_cache_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            cached_prod = ProductInput(**saved_data)
            st.session_state["photo_extracted_product"] = cached_prod
            if get_cached_image("front") or get_cached_image("back"):
                st.session_state["active_product"] = cached_prod
                st.session_state["active_source"] = f"📸 Dual-Photo Scan: {cached_prod.product_name}"
    except Exception:
        pass

# Input Mode Tabs
tab_photo, tab_bench, tab_custom = st.tabs([
    "📸 Upload Packaging Photo",
    "🧪 Benchmark Supermarket Foods",
    "✍️ Custom Product Input"
])

# ---------------------------------------------------------
# TAB 1: Multimodal Vision Upload (Dual Photo: Front & Back)
# ---------------------------------------------------------
with tab_photo:
    st.markdown("#### 📸 Upload Food Packaging Photos (Front & Back)")
    st.caption(
        "Upload photos of both the **Front of Pack** (marketing claims, brand, product name) "
        "and the **Back of Pack** (ingredients list, QUID percentages, nutrition facts). "
        "NutriPure AI cross-references both sides simultaneously using Multimodal Vision AI."
    )

    col_front, col_back = st.columns(2)

    with col_front:
        st.markdown("##### 🏷️ Photo 1: Front of Pack *(Marketing & Claims)*")
        uploaded_front = st.file_uploader(
            "Upload Front Photo:",
            type=["jpg", "jpeg", "png", "webp", "jfif", "bmp", "tiff"],
            key="front_photo_uploader",
            help="Showcases product name, brand, and front claims like '100% Atta', 'Zero Sugar'"
        )
        if uploaded_front is not None:
            st.session_state["front_image_data"] = save_uploaded_cache("front", uploaded_front)
            st.session_state["front_uploader_active"] = True
        else:
            if st.session_state.get("front_uploader_active"):
                clear_upload_cache("front")
                st.session_state["front_image_data"] = None
                st.session_state["front_uploader_active"] = False
            elif not st.session_state.get("front_image_data"):
                st.session_state["front_image_data"] = get_cached_image("front")

        front_img = st.session_state.get("front_image_data")
        if front_img:
            meta = get_cached_meta("front")
            caption = f"Front Preview ({meta.get('name', 'Uploaded')})" if meta.get("name") else "Front of Pack Preview"
            st.image(front_img, caption=caption, use_container_width=True)
        else:
            st.markdown("""
            <div style="border: 2px dashed rgba(255,255,255,0.15); border-radius:8px; padding:24px; text-align:center; color:#94A3B8;">
                📷 No front photo uploaded yet.<br/><small>Captures marketing claims & badges</small>
            </div>
            """, unsafe_allow_html=True)

    with col_back:
        st.markdown("##### 📋 Photo 2: Back of Pack *(Ingredients & Nutrition)*")
        uploaded_back = st.file_uploader(
            "Upload Back Photo:",
            type=["jpg", "jpeg", "png", "webp", "jfif", "bmp", "tiff"],
            key="back_photo_uploader",
            help="Showcases full ingredients declaration, percentages, INS numbers, and nutrition facts"
        )
        if uploaded_back is not None:
            st.session_state["back_image_data"] = save_uploaded_cache("back", uploaded_back)
            st.session_state["back_uploader_active"] = True
        else:
            if st.session_state.get("back_uploader_active"):
                clear_upload_cache("back")
                st.session_state["back_image_data"] = None
                st.session_state["back_uploader_active"] = False
            elif not st.session_state.get("back_image_data"):
                st.session_state["back_image_data"] = get_cached_image("back")

        back_img = st.session_state.get("back_image_data")
        if back_img:
            meta = get_cached_meta("back")
            caption = f"Back Preview ({meta.get('name', 'Uploaded')})" if meta.get("name") else "Back of Pack Preview"
            st.image(back_img, caption=caption, use_container_width=True)
        else:
            st.markdown("""
            <div style="border: 2px dashed rgba(255,255,255,0.15); border-radius:8px; padding:24px; text-align:center; color:#94A3B8;">
                📷 No back photo uploaded yet.<br/><small>Captures ingredients & nutrition table</small>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    # Action Bar: Quick sample loader & Reset
    col_act1, col_act2, col_act3 = st.columns([1.5, 1.2, 1.3])
    with col_act1:
        if st.button("🖼️ Try Sample Dual Photos (Front + Back)", use_container_width=True):
            front_path = os.path.join("data", "sample_products", "sample_vitawheat_front.png")
            back_path = os.path.join("data", "sample_products", "sample_vitawheat_back.png")
            if os.path.exists(front_path) and os.path.exists(back_path):
                f_img = Image.open(front_path)
                f_img.load()
                b_img = Image.open(back_path)
                b_img.load()
                st.session_state["front_image_data"] = f_img
                st.session_state["back_image_data"] = b_img
                f_img.save(os.path.join(UPLOAD_CACHE_DIR, "front.png"), format="PNG")
                b_img.save(os.path.join(UPLOAD_CACHE_DIR, "back.png"), format="PNG")
                with open(os.path.join(UPLOAD_CACHE_DIR, "front_meta.json"), "w", encoding="utf-8") as f:
                    json.dump({"name": "sample_vitawheat_front.png"}, f)
                with open(os.path.join(UPLOAD_CACHE_DIR, "back_meta.json"), "w", encoding="utf-8") as f:
                    json.dump({"name": "sample_vitawheat_back.png"}, f)
                st.session_state["photo_extracted_product"] = None
                st.rerun()

    with col_act2:
        if st.button("🧹 Clear All & Start Fresh", key="tab1_reset_btn", use_container_width=True, help="Wipes all uploaded photos, active audit targets, and resets session"):
            reset_audit_session()
            st.rerun()

    # Collect available images
    active_images = []
    if st.session_state.get("front_image_data"):
        active_images.append(st.session_state["front_image_data"])
    if st.session_state.get("back_image_data"):
        active_images.append(st.session_state["back_image_data"])

    st.markdown("---")

    # Extraction Trigger & Results
    if active_images:
        img_count = len(active_images)
        st.markdown(f"**Ready for Vision AI:** `{img_count} photo{'s' if img_count > 1 else ''} attached` &nbsp;|&nbsp; **Engine:** `{vision_extractor.active_provider_name()}`")
        
        if st.button("🔍 Extract Ingredients & Claims with Multimodal Vision AI", type="primary", use_container_width=True):
            with st.spinner(f"Analyzing {img_count} packaging photo{'s' if img_count > 1 else ''} with {vision_extractor.active_provider_name()}..."):
                try:
                    extracted = vision_extractor.extract_from_images(active_images)
                    st.session_state["photo_extracted_product"] = extracted
                    st.session_state["active_product"] = extracted
                    st.session_state["active_source"] = f"📸 Dual-Photo Scan: {extracted.product_name}"
                    st.session_state["hitl_interrupted"] = False
                    st.session_state["hitl_payload"] = None
                    st.session_state["audit_report"] = None
                    
                    try:
                        with open(os.path.join(UPLOAD_CACHE_DIR, "last_extracted.json"), "w", encoding="utf-8") as f:
                            f.write(extracted.model_dump_json())
                    except Exception:
                        pass
                        
                    st.success("Successfully analyzed packaging photos! Product loaded into LangGraph pipeline.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Vision extraction failed: {str(e)}")

        if st.session_state.get("photo_extracted_product"):
            photo_prod = st.session_state["photo_extracted_product"]
            claims_html = "".join([f'<span class="claim-tag">★ {claim}</span>' for claim in photo_prod.front_claims])
            nutri = photo_prod.nutritional_facts
            nutri_table_html = format_nutrition_table_html(nutri)

            st.markdown(f"""
            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <h3 style="margin:0 0 4px 0; color:#10B981;">{photo_prod.product_name}</h3>
                        <p style="margin:0 0 8px 0; color:#94A3B8; font-size:0.9rem;">
                            <b>Brand:</b> {photo_prod.brand} &nbsp;|&nbsp; <b>Category:</b> {photo_prod.claimed_category}
                        </p>
                    </div>
                    <span class="badge-pill" style="border-color:#10B981; color:#10B981;">Synthesized from {img_count} Image{'s' if img_count > 1 else ''}</span>
                </div>
                <div style="margin-bottom:12px;">
                    <b>Front Claims:</b><br/>
                    {claims_html if claims_html else '<span style="color:#64748B;">No claims detected</span>'}
                </div>
                <div style="display:grid; grid-template-columns: 1.1fr 0.9fr; gap: 14px; margin-top:10px;">
                    <div style="background:rgba(0,0,0,0.25); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                        <b style="color:#38BDF8; font-size:0.9rem;">📋 Back-of-Pack Ingredients Text:</b>
                        <div style="font-size:0.85rem; color:#CBD5E1; margin-top:6px; max-height:220px; overflow-y:auto; line-height:1.4;">
                            {photo_prod.raw_ingredients_text}
                        </div>
                    </div>
                    <div style="background:rgba(0,0,0,0.25); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <b style="color:#10B981; font-size:0.9rem;">📊 Nutritional Information:</b>
                            <span style="font-size:0.75rem; color:#64748B;">{f'Serve: {nutri.serving_size}' if nutri and nutri.serving_size else 'Per 100g'}</span>
                        </div>
                        <div style="font-size:0.83rem; color:#E2E8F0; max-height:220px; overflow-y:auto;">
                            {nutri_table_html}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✅ Confirm This Scanned Formulation for Audit", use_container_width=True):
                st.session_state["active_product"] = photo_prod
                st.session_state["active_source"] = f"📸 Dual-Photo Scan: {photo_prod.product_name}"
                st.session_state["hitl_interrupted"] = False
                st.session_state["audit_report"] = None
                st.success("Target updated for audit! Click the button below to run the audit.")
                st.rerun()
    else:
        st.info("👆 Upload photos of the **Front** and/or **Back** of your packaged food, or click **'Try Sample Dual Photos'** to test.")

# ---------------------------------------------------------
# TAB 2: Supermarket Benchmark Foods
# ---------------------------------------------------------
with tab_bench:
    col_sel, col_meta = st.columns([1.1, 1.9])
    with col_sel:
        product_names = [p["product_name"] for p in benchmark_products]
        chosen_name = st.selectbox("Choose a real-world product to audit:", product_names, index=0)
        selected_product_raw = next(p for p in benchmark_products if p["product_name"] == chosen_name)
        if st.button("📥 Load Selected Benchmark Product", use_container_width=True):
            st.session_state["active_product"] = build_product_input(
                id=selected_product_raw["id"],
                product_name=selected_product_raw["product_name"],
                brand=selected_product_raw["brand"],
                claimed_category=selected_product_raw["claimed_category"],
                front_claims=selected_product_raw["front_claims"],
                ingredients_text=selected_product_raw["ingredients_text"],
                nutritional_facts=selected_product_raw.get("nutritional_facts_per_100g")
            )
            st.session_state["active_source"] = f"Benchmark: {selected_product_raw['product_name']}"
            st.session_state["hitl_interrupted"] = False
            st.session_state["audit_report"] = None
            st.success(f"Loaded '{selected_product_raw['product_name']}'")
            st.rerun()
    
    with col_meta:
        claims_html = "".join([f'<span class="claim-tag">★ {claim}</span>' for claim in selected_product_raw["front_claims"]])
        st.markdown(f"""
        <div class="glass-card">
            <h4 style="margin:0 0 6px 0; color:#F1F5F9;">{selected_product_raw['product_name']}</h4>
            <p style="margin:0 0 10px 0; color:#94A3B8; font-size:0.9rem;">
                <b>Brand:</b> {selected_product_raw['brand']} &nbsp;|&nbsp; <b>Category:</b> {selected_product_raw['claimed_category']}
            </p>
            <div style="margin-top:6px;">{claims_html}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3: Custom Formulation Input
# ---------------------------------------------------------
with tab_custom:
    st.markdown("Paste custom packaging details below to audit any packaged food in your pantry:")
    c1, c2 = st.columns(2)
    with c1:
        c_name = st.text_input("Product Name", value="Instant Whole Wheat Noodles")
        c_brand = st.text_input("Brand", value="SnackCorp")
    with c2:
        c_category = st.text_input("Claimed Category", value="Health Snack")
        c_claims = st.text_input("Front Claims (comma-separated)", value="100% Atta Noodles, No Added Sugar, Zero Preservatives")
    
    c_ing = st.text_area(
        "Back-of-Pack Ingredients Text",
        value="Refined Wheat Flour (Maida) 58%, Whole Wheat Flour (Atta) 22%, Palm Oil, Salt, Sugar, Maltodextrin, Preservative [INS 211], Raising Agent [INS 500(ii)].",
        height=100
    )
    
    if st.button("📝 Load Custom Formulation", use_container_width=True):
        claims_list = [c.strip() for c in c_claims.split(",") if c.strip()]
        st.session_state["active_product"] = build_product_input(
            id="custom_food_item",
            product_name=c_name,
            brand=c_brand,
            claimed_category=c_category,
            front_claims=claims_list,
            ingredients_text=c_ing
        )
        st.session_state["active_source"] = f"Custom: {c_name}"
        st.session_state["hitl_interrupted"] = False
        st.session_state["audit_report"] = None
        st.success(f"Loaded '{c_name}' into agentic pipeline.")
        st.rerun()

# ---------------------------------------------------------
# Target For Audit Card
# ---------------------------------------------------------
selected_product = st.session_state.get("active_product")
active_source = st.session_state.get("active_source", "Benchmark")

if selected_product:
    # Notice for ghost photo scan if photos were cleared/refreshed
    if active_source.startswith("📸 Dual-Photo Scan"):
        has_any_imgs = bool(
            st.session_state.get("front_image_data") or
            st.session_state.get("back_image_data") or
            get_cached_image("front") or
            get_cached_image("back")
        )
        if not has_any_imgs:
            st.warning(f"⚠️ **Note:** Currently displaying previous audit for **{selected_product.product_name}**. To audit a different product, upload new photos in Tab 1 or click **'Clear Target'**.")

    col_card, col_reset = st.columns([4.2, 1.2])
    with col_card:
        st.markdown(f"""
        <div style="background:rgba(16, 185, 129, 0.08); border:1px solid rgba(16, 185, 129, 0.35); border-radius:10px; padding:12px 18px; margin:16px 0;">
            <span style="font-size:0.75rem; font-weight:700; color:#10B981; letter-spacing:0.06em; text-transform:uppercase;">ACTIVE AUDIT TARGET &nbsp;•&nbsp; {active_source}</span>
            <h3 style="margin:4px 0 2px 0; color:#F8FAFC;">{selected_product.product_name} <span style="font-size:0.9rem; color:#94A3B8; font-weight:400;">by {selected_product.brand}</span></h3>
            <span style="font-size:0.85rem; color:#CBD5E1;"><b>Category:</b> {selected_product.claimed_category} &nbsp;|&nbsp; <b>Ingredients Identified:</b> {len(selected_product.ingredients)} items &nbsp;|&nbsp; <b>Claims:</b> {len(selected_product.front_claims)} claims</span>
        </div>
        """, unsafe_allow_html=True)
    with col_reset:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Target", key="clear_active_prod_btn", use_container_width=True, help="Dismiss this active product and clear the audit"):
            reset_audit_session()
            st.rerun()
else:
    st.info("👆 Please upload packaging photos in **Tab 1**, select a benchmark in **Tab 2**, or enter custom formulation details in **Tab 3** to begin.")


# ---------------------------------------------------------
# Audit Execution & In-Stream HITL Checkpointing
# ---------------------------------------------------------
if selected_product:
    thread_id = f"audit_thread_{selected_product.id}"
    
    is_interrupted = st.session_state.get("hitl_interrupted") and st.session_state.get("hitl_product_id") == selected_product.id
    current_report = st.session_state.get("audit_report") if st.session_state.get("audit_product_id") == selected_product.id else None

    # Step 1: Initial Trigger Button (visible when not in an active audit or user wants to restart)
    if not is_interrupted and not current_report:
        st.write("")
        if st.button("⚡ Run Autonomous Audit with LangGraph", type="primary", use_container_width=True):
            with st.status("Executing Multi-Agent Reasoning Graph (Nodes 1-4)...", expanded=True) as status:
                st.write("🟢 **Node 1: Chemical Decoding & INS Registry Check...**")
                st.write("🟢 **Node 2: Ingesting ChromaDB Regulatory RAG & FSSAI Gazettes...**")
                st.write("🟢 **Node 3: Marketing Claim Verification & Contradiction Detection...**")
                st.write("⏸️ **Node 4: Pausing at LangGraph HITL Adjudication Gate...**")
                
                result = hitl_system.start_audit(selected_product, thread_id=thread_id)
                status.update(label="AI Analysis Complete — Paused for Human Adjudication!", state="complete", expanded=False)

            if result["status"] == "INTERRUPTED":
                st.session_state["hitl_interrupted"] = True
                st.session_state["hitl_payload"] = result["interrupt_payload"]
                st.session_state["hitl_state_values"] = result["state_values"]
                st.session_state["hitl_product_id"] = selected_product.id
                st.session_state["hitl_thread_id"] = thread_id
                st.session_state["audit_report"] = None
                st.rerun()
            else:
                st.session_state["hitl_interrupted"] = False
                st.session_state["audit_report"] = result["audit_report"]
                st.session_state["audit_product_id"] = selected_product.id
                st.rerun()

    # Step 2: INTERACTIVE HITL ADJUDICATION GATE (in-stream review)
    elif is_interrupted:
        hitl_payload = st.session_state.get("hitl_payload", {})
        contradictions = hitl_payload.get("contradictions", [])
        triggers = hitl_payload.get("dynamic_health_triggers", [])
        
        st.markdown("""
        <div style="background:rgba(245, 158, 11, 0.08); border:2px solid #F59E0B; border-radius:12px; padding:18px 22px; margin:20px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#F59E0B;">⏸️ LangGraph Human-in-the-Loop Adjudication Gate</h3>
                    <p style="margin:6px 0 0 0; color:#CBD5E1; font-size:0.92rem;">
                        The autonomous agents have finished initial claim grading and <b>paused execution</b>. As the <b>Expert Auditor</b>, adjudicate the findings below before final certification:
                    </p>
                </div>
                <span class="badge-pill" style="border-color:#F59E0B; color:#F59E0B; background:rgba(245, 158, 11, 0.15);">
                    CHECKPOINT PAUSED
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_adj1, col_adj2 = st.columns([1.1, 0.9])

        # Panel 1: Claim Adjudication
        with col_adj1:
            st.markdown("#### ⚖️ Section 1: Marketing Claim Adjudication")
            claim_decisions = {}
            if contradictions:
                st.caption("Review AI-detected marketing violations and choose your ruling:")
                for idx, c in enumerate(contradictions):
                    st.markdown(f"""
                    <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08); border-left:4px solid #EF4444; border-radius:8px; padding:12px; margin-bottom:12px;">
                        <b style="color:#FCA5A5; font-size:0.95rem;">Flagged Claim: "{c['claim']}"</b>
                        <div style="font-size:0.85rem; color:#CBD5E1; margin:4px 0;"><b>Back-of-Pack Reality:</b> {c['evidence']}</div>
                        <div style="font-size:0.8rem; color:#94A3B8;"><b>Legal Authority:</b> <i>{c.get('relevant_regulation', 'FSSAI Standards')}</i></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    choice = st.radio(
                        f"Your Adjudication for Claim #{idx+1}:",
                        [
                            "🔴 Confirm Legal Violation & Penalize Score",
                            "🟡 Downgrade to Advisory Notice (Minor Inconsistency)",
                            "⚪ Dismiss (Allow Claim as Marketing Puffery)"
                        ],
                        index=0,
                        key=f"hitl_claim_{idx}"
                    )
                    
                    if "Dismiss" in choice:
                        claim_decisions[c['claim']] = "DISMISSED"
                    elif "Downgrade" in choice:
                        claim_decisions[c['claim']] = "ADVISORY"
                    else:
                        claim_decisions[c['claim']] = "CONFIRMED"
            else:
                st.markdown('<div class="clean-card-dark" style="padding:12px;">✅ <b>Clean Label:</b> No deceptive marketing contradictions flagged by AI.</div>', unsafe_allow_html=True)

        # Panel 2: Contextual Consumer Risk Gating
        with col_adj2:
            st.markdown("#### 🩸 Section 2: Contextual Health & Consumer Profiling")
            st.caption("AI identified the following product-specific health risk triggers. Toggle if applicable to the intended consumer:")
            
            selected_conditions = {}
            if triggers:
                for t in triggers:
                    ckey = t["condition_key"]
                    val = st.checkbox(
                        f"**{t['label']}**",
                        value=False,
                        key=f"trig_chk_{ckey}",
                        help=t["evidence"]
                    )
                    st.markdown(f"<div style='font-size:0.82rem; color:#94A3B8; margin:-8px 0 10px 24px;'>↳ <i>{t['question']}</i><br/><span style='color:#64748B;'>{t['evidence']}</span></div>", unsafe_allow_html=True)
                    selected_conditions[ckey] = val
            else:
                st.markdown('<div class="clean-card-dark" style="padding:12px;">✅ No critical high-glycemic or synthetic additive triggers found.</div>', unsafe_allow_html=True)

            with st.expander("➕ Additional Consumer Health Profiles (Optional)"):
                add_pregnant = st.toggle("🤰 Pregnant / Nursing Consumer", value=False)
                add_other_allergies = st.multiselect(
                    "Additional Allergies:",
                    ["Peanuts", "Tree Nuts", "Egg", "Fish / Shellfish"],
                    default=[]
                )

        st.markdown("---")
        
        # Panel 3: Official Directive & Expert Note
        st.markdown("#### 📝 Section 3: Official Regulatory Directive & Nutritionist Notes")
        c_dir1, c_dir2 = st.columns([1, 1.2])
        with c_dir1:
            directive_choice = st.selectbox(
                "Official Regulatory Ruling:",
                [
                    "Confirm AI Findings & Issue Standard Report",
                    "Issue Formal FSSAI Non-Compliance Notice (Strict)",
                    "Certify Formulation as Compliant (Human Clearance)"
                ],
                index=0
            )
            directive_map = {
                "Confirm AI Findings & Issue Standard Report": "CONFIRM_FINDINGS",
                "Issue Formal FSSAI Non-Compliance Notice (Strict)": "ISSUE_WARNING",
                "Certify Formulation as Compliant (Human Clearance)": "CLEAR_COMPLIANT"
            }
            auditor_directive = directive_map[directive_choice]

        with c_dir2:
            expert_notes = st.text_area(
                "Auditor Clinical Notes (Optional):",
                placeholder="e.g., Reviewed Atta ratio; approved under discretionary threshold. Advised diabetic consumers to avoid due to high sugar load.",
                height=68
            )

        # Resume Button
        col_btn1, col_btn2 = st.columns([1.5, 1])
        with col_btn1:
            if st.button("🚀 Apply Human Adjudication & Finalize Audit Report", type="primary", use_container_width=True):
                with st.spinner("Resuming LangGraph from SQLite Checkpoint with Human Adjudication..."):
                    allergies = []
                    if selected_conditions.get("allergy_gluten"):
                        allergies.append("Gluten")
                    if selected_conditions.get("allergy_soy"):
                        allergies.append("Soy")
                    if selected_conditions.get("allergy_dairy"):
                        allergies.append("Dairy / Lactose")
                    allergies.extend(add_other_allergies)
                    
                    health_profile = {
                        "diabetic": selected_conditions.get("diabetic", False),
                        "hypertensive": selected_conditions.get("hypertensive", False),
                        "is_child": selected_conditions.get("is_child", False),
                        "pregnant": add_pregnant,
                        "allergies": allergies
                    }

                    adjudication_payload = {
                        "claim_adjudications": [
                            {"claim": c, "decision": d} for c, d in claim_decisions.items()
                        ],
                        "health_profile": health_profile,
                        "auditor_directive": auditor_directive,
                        "expert_notes": expert_notes.strip() if expert_notes else None
                    }

                    final_report = hitl_system.resume_audit(
                        adjudication_payload,
                        thread_id=st.session_state["hitl_thread_id"]
                    )
                    st.session_state["audit_report"] = final_report
                    st.session_state["hitl_interrupted"] = False
                    st.session_state["audit_product_id"] = selected_product.id
                    st.success("Human Adjudication applied successfully!")
                    st.rerun()
        with col_btn2:
            if st.button("❌ Cancel & Start Fresh", use_container_width=True, help="Cancel this audit and reset to a clean state"):
                reset_audit_session()
                st.rerun()

    # Step 3: DISPLAY FINAL REPORT (when completed)
    if current_report and not is_interrupted:
        report = current_report
        decoded = report.flagged_additives
        
        st.markdown("---")
        
        # Dual-Verified Certification Banner
        if report.is_human_verified:
            st.markdown("""
            <div style="background:linear-gradient(90deg, rgba(16,185,129,0.12) 0%, rgba(56,189,248,0.12) 100%); border:1px solid #10B981; border-radius:10px; padding:14px 20px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:700; color:#10B981; font-size:1.05rem; letter-spacing:0.04em;">🛡️ DUAL-VERIFIED AUDIT CERTIFICATE</span>
                    <div style="color:#E2E8F0; font-size:0.88rem; margin-top:3px;">
                        This audit was evaluated by <b>Autonomous Multimodal AI</b> and certified via <b>Human-in-the-Loop Expert Adjudication</b>.
                    </div>
                </div>
                <span class="badge-pill" style="border-color:#10B981; color:#10B981; background:rgba(16,185,129,0.15); font-size:0.85rem; padding:6px 14px;">
                    HITL CERTIFIED ✓
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        # If Auditor Directive was recorded
        if report.hitl_adjudication and (report.hitl_adjudication.expert_notes or report.hitl_adjudication.auditor_directive != "CONFIRM_FINDINGS"):
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #F59E0B; margin-bottom:16px;">
                <b style="color:#F59E0B;">🧑‍⚖️ Official Food Safety Officer Directive:</b> <code>{report.hitl_adjudication.auditor_directive}</code><br/>
                <div style="margin-top:6px; color:#CBD5E1; font-size:0.9rem;">
                    <b>Auditor Note:</b> {report.hitl_adjudication.expert_notes or 'Standard regulatory findings upheld with human confirmation.'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📊 Comprehensive Audit Verdict")
        
        # Summary Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            verdict_color = "#EF4444" if "UNHEALTHY" in report.overall_health_verdict else ("#F59E0B" if "CAUTION" in report.overall_health_verdict else "#10B981")
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; min-height:125px;">
                <span style="color:#94A3B8; font-size:0.82rem; font-weight:600; letter-spacing:0.04em;">OVERALL VERDICT</span>
                <h3 style="margin:6px 0 0 0; font-size:1.1rem; color:{verdict_color}; line-height:1.25;">
                    {report.overall_health_verdict}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            nova_name = "Ultra-Processed (UPF)" if report.nova_group == 4 else ("Processed" if report.nova_group == 3 else ("Culinary" if report.nova_group == 2 else "Minimally Processed"))
            nova_color = "#EF4444" if report.nova_group == 4 else ("#F59E0B" if report.nova_group == 3 else "#10B981")
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; min-height:125px;">
                <span style="color:#94A3B8; font-size:0.82rem; font-weight:600; letter-spacing:0.04em;">NOVA PROCESSING</span>
                <h3 style="margin:6px 0 0 0; color:#38BDF8;">Group {report.nova_group}</h3>
                <small style="color:{nova_color}; font-weight:600;">{nova_name}</small>
            </div>
            """, unsafe_allow_html=True)
            
        with m3:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; min-height:125px;">
                <span style="color:#94A3B8; font-size:0.82rem; font-weight:600; letter-spacing:0.04em;">DECEPTIVE CLAIMS</span>
                <h3 style="margin:6px 0 0 0; color:{'#EF4444' if len(report.contradictions) > 0 else '#10B981'};">
                    {len(report.contradictions)} Flagged
                </h3>
                <small style="color:#64748B;">Front Marketing Audit</small>
            </div>
            """, unsafe_allow_html=True)
            
        with m4:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; min-height:125px;">
                <span style="color:#94A3B8; font-size:0.82rem; font-weight:600; letter-spacing:0.04em;">CHEMICAL ADDITIVES</span>
                <h3 style="margin:6px 0 0 0; color:#A855F7;">{len(decoded)} Detected</h3>
                <small style="color:#64748B;">INS / E-Number Codes</small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #38BDF8; margin-bottom:1.5rem;">
            <b style="color:#38BDF8;">Executive Summary:</b> {report.executive_summary}
        </div>
        """, unsafe_allow_html=True)

        # ------------------------------------------------------------------
        # Top Section: Plain-Language Summary for Everyday Shoppers
        # ------------------------------------------------------------------
        plain_sum = generate_plain_english_summary(report, selected_product)
        
        main_sum_html = (
            f'<div style="background:linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%); '
            f'border:2px solid {plain_sum["headline_color"]}; border-radius:14px; padding:22px 26px; margin: 18px 0 24px 0; box-shadow:0 10px 30px rgba(0,0,0,0.4);">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:12px; margin-bottom:16px;">'
            f'<div><span style="font-size:0.75rem; font-weight:800; color:{plain_sum["headline_color"]}; letter-spacing:0.08em; text-transform:uppercase;">'
            f'🗣️ Plain-English Consumer Summary (What This Means For You)</span>'
            f'<h3 style="margin:4px 0 0 0; color:#F8FAFC; font-size:1.3rem;">{md_to_html(plain_sum["headline"])}</h3></div>'
            f'<span class="badge-pill" style="border-color:{plain_sum["headline_color"]}; color:{plain_sum["headline_color"]}; background:rgba(0,0,0,0.45); font-size:0.85rem; padding:6px 14px;">'
            f'JARGON-FREE GUIDE</span></div>'
            f'<div style="background:rgba(255,255,255,0.03); border-left:4px solid {plain_sum["headline_color"]}; border-radius:8px; padding:14px 18px;">'
            f'<b style="color:#F1F5F9; font-size:1.05rem;">🛒 The 10-Second Takeaway:</b>'
            f'<p style="color:#E2E8F0; font-size:0.96rem; margin:6px 0 0 0; line-height:1.6;">{md_to_html(plain_sum["bottom_line"])}</p>'
            f'</div></div>'
        )
        st.markdown(main_sum_html, unsafe_allow_html=True)
        
        # 2-Column Shopper Breakdown
        col_simp1, col_simp2 = st.columns(2)
        
        with col_simp1:
            st.markdown("##### 🔍 Marketing Claim Reality Check")
            if plain_sum['marketing_truths']:
                for m in plain_sum['marketing_truths']:
                    st.markdown(f"""
                    <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08); border-left:4px solid #EF4444; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <b style="color:#FCA5A5; font-size:0.92rem;">🏷️ Front Claim: "{md_to_html(m['claim'])}"</b>
                        <div style="color:#CBD5E1; font-size:0.88rem; margin-top:4px; line-height:1.45;">
                            <b>Real Truth:</b> {md_to_html(m['plain_truth'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="clean-card-dark">✅ <b>No deceptive claims detected:</b> The front label claims match what is in the recipe.</div>', unsafe_allow_html=True)

            if plain_sum['ingredients_plain']:
                st.markdown("##### 🍞 Primary Ingredients in Plain Words")
                for ing in plain_sum['ingredients_plain']:
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:0.88rem; color:#E2E8F0;">
                        {md_to_html(ing)}
                    </div>
                    """, unsafe_allow_html=True)

        with col_simp2:
            if plain_sum['chemicals_plain']:
                st.markdown("##### ⚗️ What the Chemical Codes (INS Numbers) Actually Are")
                for ch in plain_sum['chemicals_plain']:
                    st.markdown(f"""
                    <div style="background:rgba(168, 85, 247, 0.06); border:1px solid rgba(168, 85, 247, 0.2); border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                        <b style="color:#D8B4FE; font-size:0.9rem;">{md_to_html(ch['friendly_name'])}</b>
                        <div style="color:#CBD5E1; font-size:0.85rem; margin-top:3px;">{md_to_html(ch['simple_job'])}</div>
                    </div>
                    """, unsafe_allow_html=True)

            if plain_sum['health_cautions']:
                st.markdown("##### ⚠️ Who Should Be Extra Careful")
                for hc in plain_sum['health_cautions']:
                    st.markdown(f"""
                    <div style="background:rgba(239, 68, 68, 0.06); border:1px solid rgba(239, 68, 68, 0.2); border-radius:8px; padding:10px 14px; margin-bottom:8px; font-size:0.88rem; color:#FCA5A5;">
                        {md_to_html(hc)}
                    </div>
                    """, unsafe_allow_html=True)

            # Smart Swap Box
            st.markdown(f"""
            <div style="background:rgba(16, 185, 129, 0.08); border:1.5px solid rgba(16, 185, 129, 0.35); border-radius:10px; padding:14px 18px; margin-top:10px;">
                <b style="color:#10B981; font-size:0.95rem;">🛒 Healthy Swap / Everyday Tip:</b>
                <div style="color:#E2E8F0; font-size:0.9rem; margin-top:4px; line-height:1.5;">
                    {md_to_html(plain_sum['smart_swap'])}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔬 In-Depth Regulatory, Chemical & Scientific Audit")
        st.caption("Detailed breakdown for researchers, food safety officers, and health professionals:")

        # ------------------------------------------------------------------
        # Section A: Independent Nutritional Hazard & Critical Load Audit (WHO & ICMR-NIN)
        # ------------------------------------------------------------------
        st.markdown("#### 🚨 Independent Nutritional Hazard & Toxic Load Audit (WHO & ICMR-NIN)")
        st.caption(
            "Evaluates whether the food's nutrient concentrations exceed WHO and ICMR-NIN daily safety limits, "
            "**completely independent of whether the brand made marketing claims on the packaging**."
        )

        hazards = report.nutritional_hazards if getattr(report, "nutritional_hazards", None) else evaluate_nutritional_hazards(selected_product)
        if hazards:
            critical_hazards = [h for h in hazards if h.severity == "CRITICAL"]
            if critical_hazards:
                banner_html = (
                    '<div style="background:rgba(239,68,68,0.12); border:1px solid #EF4444; border-left:6px solid #EF4444; border-radius:8px; padding:12px 18px; margin-bottom:14px;">'
                    '<div style="font-weight:700; color:#FCA5A5; font-size:0.95rem; display:flex; align-items:center; justify-content:space-between;">'
                    '<span>⚠️ CRITICAL PHYSIOLOGICAL HAZARD DETECTED</span>'
                    '<span class="badge-high">INDEPENDENT OF CLAIMS</span>'
                    '</div>'
                    '<div style="color:#E2E8F0; font-size:0.88rem; margin-top:4px;">'
                    'Even if the manufacturer makes <b>no false claims</b> on the front packaging (or avoids front claims altogether), '
                    'this product delivers <b>excessive loads of sugar, fat, or sodium that exceed international public health safety limits</b>.'
                    '</div>'
                    '</div>'
                )
                st.markdown(banner_html, unsafe_allow_html=True)
                
            for h in hazards:
                is_crit = h.severity == "CRITICAL"
                card_border = "#EF4444" if is_crit else "#F59E0B"
                card_bg = "rgba(239, 68, 68, 0.08)" if is_crit else "rgba(245, 158, 11, 0.08)"
                badge_class = "badge-high" if is_crit else "badge-mod"
                
                parts = [
                    f'<div style="background:{card_bg}; border:1px solid {card_border}; border-left:5px solid {card_border}; border-radius:8px; padding:14px; margin-bottom:12px;">',
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">',
                    f'<span style="font-weight:700; color:#F8FAFC; font-size:1rem;">🚩 {h.headline}</span>',
                    f'<span class="{badge_class}">{h.severity} HAZARD</span>',
                    f'</div>',
                    f'<div style="color:#CBD5E1; font-size:0.88rem; margin-top:6px; line-height:1.45;">{h.explanation}</div>'
                ]
                
                # Visual comparison calculation for sugar or sodium
                if h.nutrient == "Total Sugars" and h.amount_per_100g:
                    pct_who = min(int((h.amount_per_100g / 25.0) * 100), 200)
                    progress_color = "#EF4444" if pct_who >= 90 else "#F59E0B"
                    parts.append(
                        f'<div style="margin-top:8px; background:rgba(0,0,0,0.3); border-radius:6px; padding:8px 10px;">'
                        f'<div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#CBD5E1; margin-bottom:4px;">'
                        f'<span><b>WHO Daily Optimal Sugar Allowance (25g / 6 tsp/day):</b></span>'
                        f'<span style="color:{progress_color}; font-weight:700;">{pct_who}% Exhausted per 100g</span>'
                        f'</div>'
                        f'<div style="background:rgba(255,255,255,0.1); border-radius:4px; height:8px; width:100%; overflow:hidden;">'
                        f'<div style="background:{progress_color}; height:8px; width:{min(pct_who, 100)}%;"></div>'
                        f'</div>'
                        f'</div>'
                    )
                elif h.nutrient == "Sodium" and h.amount_per_100g:
                    pct_sod = min(int((h.amount_per_100g / 2000.0) * 100), 200)
                    progress_color = "#EF4444" if pct_sod >= 30 else "#F59E0B"
                    parts.append(
                        f'<div style="margin-top:8px; background:rgba(0,0,0,0.3); border-radius:6px; padding:8px 10px;">'
                        f'<div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#CBD5E1; margin-bottom:4px;">'
                        f'<span><b>WHO Daily Maximum Sodium Ceiling (2,000mg/day):</b></span>'
                        f'<span style="color:{progress_color}; font-weight:700;">{pct_sod}% Exhausted per 100g</span>'
                        f'</div>'
                        f'<div style="background:rgba(255,255,255,0.1); border-radius:4px; height:8px; width:100%; overflow:hidden;">'
                        f'<div style="background:{progress_color}; height:8px; width:{min(pct_sod * 3, 100)}%;"></div>'
                        f'</div>'
                        f'</div>'
                    )
                    
                if h.clinical_risk:
                    parts.append(
                        f'<div style="margin-top:6px; font-size:0.85rem; color:#FECACA;"><b>🩺 Clinical Metabolic Risk:</b> {h.clinical_risk}</div>'
                    )
                    
                parts.append(
                    f'<div style="font-size:0.8rem; color:#94A3B8; margin-top:8px; border-top:1px dashed rgba(255,255,255,0.1); padding-top:6px;">'
                    f'<b>Benchmark Reference:</b> <i>{h.guideline_source}</i>'
                    f'</div>'
                )
                parts.append('</div>')
                
                st.markdown("".join(parts), unsafe_allow_html=True)
        else:
            st.markdown('<div class="clean-card-dark">✅ <b>Safe Nutritional Profile:</b> Sugar, trans fats, saturated fat, and sodium concentrations are within healthy dietary limits established by WHO & ICMR-NIN.</div>', unsafe_allow_html=True)

        # ------------------------------------------------------------------
        # Section B: Understanding NOVA Food Processing (Groups 1 to 4 Demystified)
        # ------------------------------------------------------------------
        st.markdown("#### 📖 Understanding NOVA Processing & UPF Classification")
        nova_exp = report.nova_explanation if getattr(report, "nova_explanation", None) else generate_nova_explanation(report.nova_group, selected_product, decoded, report.disguised_sugars_found)
        
        with st.expander(f"ℹ️ What is NOVA Group {report.nova_group}? (Click to view full scientific breakdown of all 4 groups)", expanded=(report.nova_group == 4)):
            nova_grid_html = (
                '<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:16px;">'
                '<div style="background:rgba(16,185,129,0.1); border:1px solid #10B981; border-radius:8px; padding:10px; text-align:center;">'
                '<span style="background:#10B981; color:white; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:10px;">GROUP 1</span>'
                '<h5 style="margin:6px 0 2px 0; color:#10B981; font-size:0.9rem;">Unprocessed</h5>'
                '<small style="color:#94A3B8; font-size:0.75rem; line-height:1.2; display:block;">Whole foods: fresh fruits, vegetables, oats, pulses, plain milk</small>'
                '</div>'
                '<div style="background:rgba(234,179,8,0.1); border:1px solid #EAB308; border-radius:8px; padding:10px; text-align:center;">'
                '<span style="background:#EAB308; color:black; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:10px;">GROUP 2</span>'
                '<h5 style="margin:6px 0 2px 0; color:#EAB308; font-size:0.9rem;">Culinary Ingredients</h5>'
                '<small style="color:#94A3B8; font-size:0.75rem; line-height:1.2; display:block;">Cooking essentials: oils, butter, table salt, sugar, vinegar</small>'
                '</div>'
                '<div style="background:rgba(249,115,22,0.1); border:1px solid #F97316; border-radius:8px; padding:10px; text-align:center;">'
                '<span style="background:#F97316; color:white; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:10px;">GROUP 3</span>'
                '<h5 style="margin:6px 0 2px 0; color:#F97316; font-size:0.9rem;">Processed Foods</h5>'
                '<small style="color:#94A3B8; font-size:0.75rem; line-height:1.2; display:block;">Simple products: artisan bread, cheese, canned beans in brine</small>'
                '</div>'
                '<div style="background:rgba(239,68,68,0.15); border:2px solid #EF4444; border-radius:8px; padding:10px; text-align:center;">'
                '<span style="background:#EF4444; color:white; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:10px;">GROUP 4 (UPF)</span>'
                '<h5 style="margin:6px 0 2px 0; color:#FCA5A5; font-size:0.9rem;">Ultra-Processed</h5>'
                '<small style="color:#CBD5E1; font-size:0.75rem; line-height:1.2; display:block;">Industrial formulations: emulsifiers, artificial flavors, 5+ ingredients</small>'
                '</div>'
                '</div>'
            )
            st.markdown(nova_grid_html, unsafe_allow_html=True)
            
            st.markdown(f"##### 🔍 Classification Rationale for `{report.product_name}` (NOVA Group {nova_exp.group}: {nova_exp.group_name})")
            st.markdown(f"<p style='color:#CBD5E1; font-size:0.9rem;'>{nova_exp.definition}</p>", unsafe_allow_html=True)
            
            c_nv1, c_nv2 = st.columns(2)
            with c_nv1:
                st.markdown("**🔬 Specific Classification Triggers Detected in Formulation:**")
                for r in nova_exp.classification_reasons:
                    st.markdown(f"- {r}")
                if nova_exp.triggering_substances:
                    st.markdown("**🧪 Triggering Industrial Substances & Cosmetic Additives:**")
                    for ts in nova_exp.triggering_substances:
                        st.markdown(f"- <code>{ts}</code>", unsafe_allow_html=True)
                        
            with c_nv2:
                st.markdown("**🩺 Documented Clinical Risks of Ultra-Processed Foods:**")
                clinical_box_html = (
                    '<div style="background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; font-size:0.87rem; color:#CBD5E1; line-height:1.5;">'
                    f'{nova_exp.health_implications}'
                    '<div style="margin-top:8px; font-size:0.78rem; color:#94A3B8; border-top:1px dashed rgba(255,255,255,0.1); padding-top:6px;">'
                    '<b>Scientific Authorities:</b> Carlos Monteiro et al. (University of São Paulo), UN Food and Agriculture Organization (FAO), World Health Organization (WHO), and BMJ 2024 Global Umbrella Review.'
                    '</div>'
                    '</div>'
                )
                st.markdown(clinical_box_html, unsafe_allow_html=True)

        # ------------------------------------------------------------------
        # Section C: Personalized Health Alerts (HITL)
        # ------------------------------------------------------------------
        st.markdown("#### 🧑‍⚕️ Personalized Medical Warnings (HITL)")
        if report.user_health_alerts:
            for alert in report.user_health_alerts:
                st.markdown(f'<div class="alert-card-dark">⚠️ <b>Medical Contraindication:</b> {alert}</div>', unsafe_allow_html=True)
        elif report.is_human_verified:
            st.markdown('<div class="clean-card-dark">✅ <b>Medical Check Passed:</b> No critical contraindications found for the consumer profile reviewed during HITL adjudication.</div>', unsafe_allow_html=True)
        else:
            st.caption("ℹ️ Health gating alerts will be verified by the Human-in-the-Loop review.")

        # ------------------------------------------------------------------
        # Section D: The "Lie-Buster" Marketing Claims Audit
        # ------------------------------------------------------------------
        st.markdown("#### 🚨 The 'Lie-Buster' Marketing Claims Audit")
        if report.contradictions:
            for c in report.contradictions:
                st.markdown(f"""
                <div class="violation-card-dark">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#FCA5A5;">❌ Claim: "{c.claim}"</h4>
                        <span class="badge-high">{c.severity} SEVERITY</span>
                    </div>
                    <p style="margin:8px 0 4px 0; color:#E2E8F0;"><b>Back-of-Pack Reality:</b> {c.evidence}</p>
                    <p style="margin:0; color:#CBD5E1; font-size:0.88rem;"><b>Legal Authority:</b> <i>{c.relevant_regulation}</i></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="clean-card-dark">✅ <b>Clean Label:</b> No active deceptive marketing contradictions (or all flagged claims were dismissed/cleared by Human Auditor).</div>', unsafe_allow_html=True)

        # ------------------------------------------------------------------
        # Section E: Chemical Additive & E-Number Breakdown
        # ------------------------------------------------------------------
        st.markdown("#### 🧪 Decoded Chemical Additives & E-Numbers")
        if decoded:
            for add in decoded:
                badge_class = "badge-safe" if add.risk_level == "Safe" else ("badge-mod" if add.risk_level in ["Low", "Moderate"] else "badge-high")
                warning = "; ".join(add.health_warnings) if add.health_warnings else "Recognized safe under permissible limits."
                st.markdown(f"""
                <div class="glass-card" style="padding:0.9rem 1.2rem; margin-bottom:0.6rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; color:#F8FAFC; font-size:1rem;">{add.code}</span>
                            <span style="color:#94A3B8;"> — {add.chemical_name}</span>
                            <span style="margin-left:8px; font-size:0.8rem; color:#64748B;">({add.category})</span>
                        </div>
                        <span class="{badge_class}">{add.risk_level} Risk</span>
                    </div>
                    <div style="font-size:0.85rem; color:#CBD5E1; margin-top:5px;">
                        <b>Health Advisory:</b> {warning}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="clean-card-dark">✅ <b>Zero Synthetic Additives:</b> No chemical INS/E-numbers detected in formulation.</div>', unsafe_allow_html=True)

        # ------------------------------------------------------------------
        # Section F: Raw Ingredients Transparency (QUID)
        # ------------------------------------------------------------------
        with st.expander("🔍 View Raw Extracted Ingredients & Weight Percentages (QUID)"):
            st.markdown(f"**Raw Text:** `{selected_product.raw_ingredients_text}`")
            st.table([{
                "Ingredient Name": ing.name,
                "Declared %": f"{ing.percentage}%" if ing.percentage else "Not Declared",
                "Is Additive": "Yes" if ing.is_additive else "No",
                "INS Code": ing.ins_code or "None"
            } for ing in selected_product.ingredients])

        # ------------------------------------------------------------------
        # Section G: Full Nutritional Declaration Table
        # ------------------------------------------------------------------
        if selected_product.nutritional_facts:
            nf = selected_product.nutritional_facts
            has_table = any(v is not None for v in [nf.energy_kcal, nf.carbohydrates_g, nf.total_fat_g, nf.protein_g])
            if has_table:
                st.markdown("#### 📊 Full Nutritional Declaration Table (Per 100g)")

                col_n1, col_n2, col_n3, col_n4 = st.columns(4)
                with col_n1:
                    st.metric("Energy", f"{nf.energy_kcal or 0:.0f} kcal")
                with col_n2:
                    st.metric("Protein", f"{nf.protein_g or 0:.1f} g")
                with col_n3:
                    st.metric("Carbohydrates", f"{nf.carbohydrates_g or 0:.1f} g")
                with col_n4:
                    st.metric("Total Sugars", f"{nf.total_sugars_g or 0:.1f} g", delta=f"{nf.added_sugars_g or 0:.1f}g Added", delta_color="inverse")

                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1:
                    st.metric("Total Fat", f"{nf.total_fat_g or 0:.1f} g")
                with col_f2:
                    st.metric("Saturated Fat", f"{nf.saturated_fat_g or 0:.1f} g")
                with col_f3:
                    st.metric("Trans Fat", f"{nf.trans_fat_g or 0:.2f} g")
                with col_f4:
                    st.metric("Sodium", f"{nf.sodium_mg or 0:.0f} mg")

        st.markdown("---")
        col_rst1, col_rst2, col_rst3 = st.columns([1.5, 1.8, 2])
        with col_rst1:
            if st.button("🔄 Re-Audit or Adjust Ruling", use_container_width=True):
                st.session_state["hitl_interrupted"] = False
                st.session_state["audit_report"] = None
                st.rerun()
        with col_rst2:
            if st.button("🧹 Audit Another Product / Start Fresh", use_container_width=True, help="Wipes current audit report and starts fresh"):
                reset_audit_session()
                st.rerun()


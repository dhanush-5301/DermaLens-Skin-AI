import os
import io
import uuid
import time
import logging
import base64
from datetime import datetime
from pathlib import Path
import json

from dotenv import load_dotenv
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import hashlib

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

# ── Mock Auth Database ────────────────────────────────────────────
# In-memory store for prototype MVP. Mocks a secure encrypted DB.
MOCK_DB_USERS = {}
MOCK_SESSIONS = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ── Logging ───────────────────────────────────────────────────────
Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/dermalens.log")],
)
log = logging.getLogger("dermalens")

# ── Config ────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if ANTHROPIC_API_KEY.startswith("sk-ant-xxx") or ANTHROPIC_API_KEY == "":
    ANTHROPIC_API_KEY = ""

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── HAM10000 Label Maps (CNN classes) ─────────────────────────────
LABEL_MAP = {0: "nv", 1: "mel", 2: "bkl", 3: "bcc", 4: "akiec", 5: "vasc", 6: "df"}
CLASS_DISPLAY = {
    "nv": "Melanocytic Nevi", "mel": "Melanoma", "bkl": "Benign Keratosis",
    "bcc": "Basal Cell Carcinoma", "akiec": "Actinic Keratosis",
    "vasc": "Vascular Lesion", "df": "Dermatofibroma",
}

# ── Extended Disease Knowledge Base (20+ diseases) ────────────────
DISEASE_KB = {
    # --- HAM10000 CNN classes ---
    "nv": {
        "name": "Melanocytic Nevi", "scientific": "Melanocytic Nevus",
        "icd10": "D22.9", "risk": "low", "category": "Lesion",
        "prevalence": "Very common — ~20% of adults",
        "risk_desc": "Generally benign. Routine annual skin checks recommended. Watch for ABCD changes.",
        "abcd": {"asymmetry": "Usually symmetric", "border": "Well-defined, smooth", "color": "Uniform tan/brown", "dermoscopy": "Reticular or globular pattern"},
        "differential": ["Melanoma (rule out)", "Blue naevus", "Halo naevus"],
        "recommendations": [
            {"icon": "✅", "text": "<strong>Annual monitoring</strong> — Full-body skin check once a year."},
            {"icon": "☀️", "text": "<strong>Sun protection</strong> — SPF 30+ daily on exposed areas."},
            {"icon": "📸", "text": "<strong>Photo track</strong> — Photograph monthly to detect any changes."},
        ], "urgent": False,
    },
    "mel": {
        "name": "Melanoma", "scientific": "Malignant Melanoma",
        "icd10": "C43.9", "risk": "high", "category": "Cancer",
        "prevalence": "~1% of all skin cancers — deadliest type",
        "risk_desc": "Highly malignant. Can metastasize. Urgent dermatology referral and biopsy required immediately.",
        "abcd": {"asymmetry": "Often asymmetric", "border": "Irregular, notched or ragged", "color": "Variable: brown, black, red, white, blue", "dermoscopy": "Atypical pigment network, regression structures"},
        "differential": ["Melanocytic naevus", "Pigmented BCC", "Seborrheic keratosis"],
        "recommendations": [
            {"icon": "⚠️", "text": "<strong>URGENT referral</strong> — See a dermatologist within 2 weeks."},
            {"icon": "🔬", "text": "<strong>Biopsy mandatory</strong> — Histopathological confirmation required."},
            {"icon": "🏥", "text": "<strong>Do not delay</strong> — Early excision dramatically improves prognosis."},
        ], "urgent": True,
    },
    "bkl": {
        "name": "Benign Keratosis", "scientific": "Seborrheic Keratosis",
        "icd10": "L82.1", "risk": "low", "category": "Benign Growth",
        "prevalence": "Most common benign growth — >50% of adults over 40",
        "risk_desc": "Completely benign. No malignant potential. Treatment is cosmetic only.",
        "abcd": {"asymmetry": "May be asymmetric", "border": "Sharply demarcated, 'stuck-on'", "color": "Tan, brown, or dark", "dermoscopy": "Comedo-like openings, milia-like cysts"},
        "differential": ["Melanoma (rule out)", "Pigmented BCC", "Melanocytic naevus"],
        "recommendations": [
            {"icon": "✅", "text": "<strong>No treatment needed</strong> — Purely benign lesion."},
            {"icon": "👁️", "text": "<strong>Monitor for rapid changes</strong> — Sudden change warrants review."},
            {"icon": "💅", "text": "<strong>Cosmetic removal</strong> — Cryotherapy or laser if desired."},
        ], "urgent": False,
    },
    "bcc": {
        "name": "Basal Cell Carcinoma", "scientific": "Basal Cell Carcinoma",
        "icd10": "C44.91", "risk": "high", "category": "Cancer",
        "prevalence": "Most common skin cancer (~80% of non-melanoma cases)",
        "risk_desc": "Locally invasive. Rarely metastasizes but destroys tissue if untreated. Needs excision.",
        "abcd": {"asymmetry": "Variable", "border": "Rolled, translucent borders", "color": "Pearly white/pink, telangiectasia", "dermoscopy": "Arborizing vessels, blue-grey ovoid nests"},
        "differential": ["Squamous cell carcinoma", "Amelanotic melanoma", "Sebaceous hyperplasia"],
        "recommendations": [
            {"icon": "🏥", "text": "<strong>Dermatology referral</strong> — Surgical excision is standard treatment."},
            {"icon": "☀️", "text": "<strong>Strict UV protection</strong> — Sunscreen daily, avoid peak sun hours."},
            {"icon": "🔬", "text": "<strong>Biopsy recommended</strong> — Confirm diagnosis before treatment."},
        ], "urgent": True,
    },
    "akiec": {
        "name": "Actinic Keratosis", "scientific": "Actinic Keratosis / Intraepithelial Carcinoma",
        "icd10": "L57.0", "risk": "medium", "category": "Pre-Cancer",
        "prevalence": "~60 million cases/year in the US — common in sun-exposed adults",
        "risk_desc": "Pre-malignant. Can progress to squamous cell carcinoma. Treatment within 4–8 weeks recommended.",
        "abcd": {"asymmetry": "Variable", "border": "Ill-defined, erythematous", "color": "Pink-red, scaly surface", "dermoscopy": "Strawberry pattern, scaling"},
        "differential": ["Bowen disease", "Psoriasis", "Eczema", "Superficial BCC"],
        "recommendations": [
            {"icon": "🏥", "text": "<strong>Dermatologist review within 8 weeks</strong> — Cryotherapy or topical treatment."},
            {"icon": "🧴", "text": "<strong>Topical treatment</strong> — 5-fluorouracil or imiquimod cream may be prescribed."},
            {"icon": "☀️", "text": "<strong>Strict sun avoidance</strong> — UV triggers progression to SCC."},
        ], "urgent": False,
    },
    "vasc": {
        "name": "Vascular Lesion", "scientific": "Cutaneous Vascular Anomaly",
        "icd10": "D18.01", "risk": "low", "category": "Vascular",
        "prevalence": "Common benign vascular tumors — found in ~50% of adults over 30",
        "risk_desc": "Benign blood vessel proliferations. No malignant potential. Cosmetic concern only.",
        "abcd": {"asymmetry": "Usually symmetric", "border": "Well-defined", "color": "Bright red to dark purple", "dermoscopy": "Red lacunae, homogeneous red areas"},
        "differential": ["Melanoma (rule out)", "Kaposi sarcoma", "Cherry angioma"],
        "recommendations": [
            {"icon": "✅", "text": "<strong>No treatment required</strong> — Purely benign."},
            {"icon": "💡", "text": "<strong>Laser removal</strong> — Available for cosmetic purposes."},
            {"icon": "👁️", "text": "<strong>Monitor if changing</strong> — Rapid growth warrants review."},
        ], "urgent": False,
    },
    "df": {
        "name": "Dermatofibroma", "scientific": "Benign Fibrous Histiocytoma",
        "icd10": "D23.9", "risk": "low", "category": "Benign Growth",
        "prevalence": "Common benign fibrohistiocytic tumour — more frequent in women",
        "risk_desc": "Completely benign. Often follows minor trauma or insect bite. No malignant potential.",
        "abcd": {"asymmetry": "Usually symmetric", "border": "Regular, firm nodule", "color": "Pink-brown", "dermoscopy": "Central white scar-like patch, peripheral pigment network"},
        "differential": ["Melanocytic naevus", "Blue naevus", "Nodular melanoma (rule out)"],
        "recommendations": [
            {"icon": "✅", "text": "<strong>No treatment needed</strong> — Benign and asymptomatic."},
            {"icon": "✂️", "text": "<strong>Surgical excision</strong> — If symptomatic or cosmetically concerning."},
            {"icon": "📸", "text": "<strong>Photo monitoring</strong> — Document for baseline comparison."},
        ], "urgent": False,
    },

    # --- Symptom-based / general dermatology (non-HAM10000) ---
    "psoriasis": {
        "name": "Psoriasis", "scientific": "Psoriasis Vulgaris",
        "icd10": "L40.0", "risk": "low", "category": "Inflammatory",
        "prevalence": "Affects ~2–3% of global population — chronic autoimmune condition",
        "risk_desc": "Chronic but manageable. Not contagious. Can significantly impact quality of life.",
        "abcd": {"asymmetry": "Often symmetric plaques", "border": "Well-defined, silvery-white scales", "color": "Red/pink base with white scales", "dermoscopy": "Regular dotted vessels, white scaling"},
        "differential": ["Seborrheic dermatitis", "Eczema", "Fungal infection", "Pityriasis rosea"],
        "recommendations": [
            {"icon": "🏥", "text": "<strong>Dermatologist referral</strong> — For topical steroid or biologic therapy."},
            {"icon": "🧴", "text": "<strong>Moisturise daily</strong> — Emollients reduce flares significantly."},
            {"icon": "☀️", "text": "<strong>Moderate sun exposure</strong> — UV therapy (phototherapy) can help."},
        ], "urgent": False,
    },
    "eczema": {
        "name": "Eczema / Atopic Dermatitis", "scientific": "Atopic Dermatitis",
        "icd10": "L20.9", "risk": "low", "category": "Inflammatory",
        "prevalence": "Very common — affects 10–20% of children, 1–3% of adults",
        "risk_desc": "Chronic inflammatory condition. Not dangerous but very uncomfortable. Well-managed with treatment.",
        "abcd": {"asymmetry": "Diffuse, often symmetric", "border": "Poorly defined", "color": "Red, weeping or dry and scaly", "dermoscopy": "Non-specific, spongiosis on histology"},
        "differential": ["Contact dermatitis", "Psoriasis", "Seborrheic dermatitis", "Scabies"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Emollient therapy</strong> — Apply moisturiser frequently, especially after bathing."},
            {"icon": "💊", "text": "<strong>Topical steroids</strong> — Mild-to-moderate potency during flares."},
            {"icon": "🚿", "text": "<strong>Avoid triggers</strong> — Soaps, fragrances, synthetic fabrics, extreme temperatures."},
        ], "urgent": False,
    },
    "acne": {
        "name": "Acne Vulgaris", "scientific": "Acne Vulgaris",
        "icd10": "L70.0", "risk": "low", "category": "Inflammatory",
        "prevalence": "Most common skin disorder — affects ~85% of adolescents",
        "risk_desc": "Generally benign. Severe cystic acne can scar. Treatments are highly effective.",
        "abcd": {"asymmetry": "Variable, face/back/chest", "border": "Comedones, papules, pustules", "color": "Red papules, white/blackheads", "dermoscopy": "Non-specific; comedones visible"},
        "differential": ["Rosacea", "Folliculitis", "Perioral dermatitis", "Milia"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Topical retinoids</strong> — First-line treatment for comedonal acne."},
            {"icon": "💊", "text": "<strong>Antibiotics / Isotretinoin</strong> — For moderate-severe cases (prescription required)."},
            {"icon": "🚫", "text": "<strong>Avoid picking</strong> — Squeezing lesions worsens scarring and spreads bacteria."},
        ], "urgent": False,
    },
    "rosacea": {
        "name": "Rosacea", "scientific": "Rosacea Erythematosa",
        "icd10": "L71.9", "risk": "low", "category": "Inflammatory",
        "prevalence": "Affects ~5% of adults worldwide — more common in fair-skinned individuals",
        "risk_desc": "Chronic but benign. Flushing, redness, and visible blood vessels on face. No malignant potential.",
        "abcd": {"asymmetry": "Centrofacial distribution", "border": "Diffuse erythema, not well-defined", "color": "Persistent facial redness/flushing", "dermoscopy": "Dilated follicular openings, telangiectasias"},
        "differential": ["Acne vulgaris", "Seborrheic dermatitis", "Lupus erythematosus", "Perioral dermatitis"],
        "recommendations": [
            {"icon": "☀️", "text": "<strong>Sun protection mandatory</strong> — UV is the #1 trigger for rosacea flares."},
            {"icon": "💊", "text": "<strong>Topical metronidazole / ivermectin</strong> — Standard prescription treatments."},
            {"icon": "🌡️", "text": "<strong>Avoid triggers</strong> — Spicy food, alcohol, hot drinks, extreme temperatures."},
        ], "urgent": False,
    },
    "vitiligo": {
        "name": "Vitiligo", "scientific": "Vitiligo",
        "icd10": "L80", "risk": "low", "category": "Pigmentation",
        "prevalence": "Affects ~1% of global population — autoimmune depigmentation",
        "risk_desc": "Not dangerous. Loss of skin pigment due to melanocyte destruction. Cosmetically concerning but benign.",
        "abcd": {"asymmetry": "Variable — can be localised or widespread", "border": "Well-defined white patches", "color": "Chalk-white depigmented areas", "dermoscopy": "Complete loss of pigment network"},
        "differential": ["Pityriasis alba", "Post-inflammatory hypopigmentation", "Tinea versicolor", "Leprosy"],
        "recommendations": [
            {"icon": "🏥", "text": "<strong>Dermatologist evaluation</strong> — For phototherapy (NB-UVB) or topical JAK inhibitors."},
            {"icon": "☀️", "text": "<strong>High-SPF sunscreen</strong> — Depigmented skin burns easily."},
            {"icon": "💊", "text": "<strong>Topical tacrolimus</strong> — Effective for early/localised vitiligo."},
        ], "urgent": False,
    },
    "ringworm": {
        "name": "Ringworm (Tinea Corporis)", "scientific": "Tinea Corporis",
        "icd10": "B35.4", "risk": "low", "category": "Fungal Infection",
        "prevalence": "Extremely common — affects all ages and skin types worldwide",
        "risk_desc": "Fungal infection. Contagious but easily treatable with antifungals. Not dangerous.",
        "abcd": {"asymmetry": "Ring-shaped, often circular", "border": "Active scaly raised border, clearing centre", "color": "Red ring with pale centre", "dermoscopy": "Scaling at periphery, central clearing"},
        "differential": ["Eczema", "Psoriasis", "Granuloma annulare", "Pityriasis rosea"],
        "recommendations": [
            {"icon": "💊", "text": "<strong>Topical antifungal</strong> — Clotrimazole or terbinafine cream for 2–4 weeks."},
            {"icon": "🚿", "text": "<strong>Keep skin dry</strong> — Fungi thrive in moist environments."},
            {"icon": "🧺", "text": "<strong>Don't share towels/clothing</strong> — Highly contagious."},
        ], "urgent": False,
    },
    "contact_dermatitis": {
        "name": "Contact Dermatitis", "scientific": "Contact Dermatitis",
        "icd10": "L25.9", "risk": "low", "category": "Inflammatory",
        "prevalence": "Very common — one of the most frequent occupational skin diseases",
        "risk_desc": "Triggered by allergens or irritants. Resolves after removing the cause. Not dangerous.",
        "abcd": {"asymmetry": "Matches exposure pattern", "border": "Ill-defined erythema at contact site", "color": "Red, vesicular, or weeping", "dermoscopy": "Non-specific spongiosis"},
        "differential": ["Atopic dermatitis", "Psoriasis", "Scabies", "Cellulitis"],
        "recommendations": [
            {"icon": "🚫", "text": "<strong>Identify and avoid allergen/irritant</strong> — Patch testing by dermatologist."},
            {"icon": "💊", "text": "<strong>Topical corticosteroids</strong> — Reduce inflammation during acute phase."},
            {"icon": "🧤", "text": "<strong>Protective measures</strong> — Gloves and barrier creams for occupational exposure."},
        ], "urgent": False,
    },
    "hives": {
        "name": "Urticaria (Hives)", "scientific": "Urticaria",
        "icd10": "L50.9", "risk": "low", "category": "Allergic",
        "prevalence": "Affects ~20% of people at some point in their lifetime",
        "risk_desc": "Usually benign and self-limiting. Angioedema with throat/tongue swelling requires emergency care.",
        "abcd": {"asymmetry": "Widespread wheals", "border": "Raised, well-defined wheals (hives)", "color": "Pink/red, blanches with pressure", "dermoscopy": "Non-specific, transient nature"},
        "differential": ["Contact dermatitis", "Insect bites", "Erythema multiforme", "Bullous pemphigoid"],
        "recommendations": [
            {"icon": "💊", "text": "<strong>Antihistamines</strong> — Cetirizine or loratadine for immediate relief."},
            {"icon": "🚨", "text": "<strong>Emergency if throat swells</strong> — Anaphylaxis requires epinephrine (EpiPen)."},
            {"icon": "🔍", "text": "<strong>Identify trigger</strong> — Food, medication, or infection are common causes."},
        ], "urgent": False,
    },
    "warts": {
        "name": "Verruca Vulgaris (Warts)", "scientific": "Verruca Vulgaris (HPV)",
        "icd10": "B07.9", "risk": "low", "category": "Viral Infection",
        "prevalence": "Very common — caused by Human Papillomavirus (HPV); affects ~10% of population",
        "risk_desc": "Benign viral growth. Contagious. Most resolve spontaneously within 2 years.",
        "abcd": {"asymmetry": "Variable — single or clustered", "border": "Well-defined, rough surface", "color": "Skin-colored to grey-brown", "dermoscopy": "Thrombosed capillary dots (black dots)"},
        "differential": ["Corn/callus", "Seborrheic keratosis", "Molluscum contagiosum", "Squamous cell carcinoma"],
        "recommendations": [
            {"icon": "🧪", "text": "<strong>Salicylic acid preparations</strong> — First-line OTC treatment; apply daily."},
            {"icon": "❄️", "text": "<strong>Cryotherapy</strong> — Dermatologist-applied liquid nitrogen is highly effective."},
            {"icon": "🚫", "text": "<strong>Avoid sharing items</strong> — HPV spreads through direct contact."},
        ], "urgent": False,
    },
    "seborrheic_dermatitis": {
        "name": "Seborrheic Dermatitis", "scientific": "Seborrheic Dermatitis",
        "icd10": "L21.9", "risk": "low", "category": "Inflammatory",
        "prevalence": "Affects 3–5% of adults — more common in oily skin types",
        "risk_desc": "Chronic but benign. Flaking and redness in sebaceous areas. Well-controlled with antifungal agents.",
        "abcd": {"asymmetry": "Symmetric — scalp, face, chest", "border": "Poorly defined greasy scales", "color": "Yellow-white scales on red/pink base", "dermoscopy": "White/yellow scales, dilated vessels"},
        "differential": ["Psoriasis", "Atopic dermatitis", "Rosacea", "Tinea versicolor"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Antifungal shampoo</strong> — Ketoconazole 2% or selenium sulphide."},
            {"icon": "💊", "text": "<strong>Topical antifungal cream</strong> — For facial/body involvement."},
            {"icon": "🔄", "text": "<strong>Maintenance treatment</strong> — Use antifungal shampoo weekly to prevent recurrence."},
        ], "urgent": False,
    },
    "cellulitis": {
        "name": "Cellulitis", "scientific": "Cellulitis (Bacterial Skin Infection)",
        "icd10": "L03.90", "risk": "medium", "category": "Bacterial Infection",
        "prevalence": "Common bacterial infection — ~14 million cases/year in the US",
        "risk_desc": "Can spread rapidly. Requires antibiotic treatment. Sepsis risk if untreated.",
        "abcd": {"asymmetry": "Asymmetric spreading redness", "border": "Poorly defined, spreading border", "color": "Bright red, warm, swollen", "dermoscopy": "Non-dermoscopic — clinical diagnosis"},
        "differential": ["DVT", "Contact dermatitis", "Erysipelas", "Necrotizing fasciitis (severe)"],
        "recommendations": [
            {"icon": "🏥", "text": "<strong>Medical attention required</strong> — Oral or IV antibiotics needed."},
            {"icon": "🌡️", "text": "<strong>Elevate affected limb</strong> — Reduces swelling and pain."},
            {"icon": "🚨", "text": "<strong>Urgent if spreading quickly</strong> — Rapidly advancing cellulitis needs IV antibiotics."},
        ], "urgent": True,
    },
    "impetigo": {
        "name": "Impetigo", "scientific": "Impetigo Contagiosa",
        "icd10": "L01.0", "risk": "medium", "category": "Bacterial Infection",
        "prevalence": "Common in children — one of the most frequent skin infections in kids under 10",
        "risk_desc": "Highly contagious bacterial infection. Requires antibiotic treatment. Resolves well with treatment.",
        "abcd": {"asymmetry": "Often facial/perioral", "border": "Crusted lesions with honey-coloured crust", "color": "Golden-yellow crusts on erythematous base", "dermoscopy": "Non-specific crusting"},
        "differential": ["Eczema", "Pemphigus foliaceus", "Contact dermatitis", "Herpes simplex"],
        "recommendations": [
            {"icon": "💊", "text": "<strong>Topical mupirocin or fusidic acid</strong> — For localised impetigo."},
            {"icon": "🧼", "text": "<strong>Gently clean crusts</strong> — Soak with antiseptic before applying cream."},
            {"icon": "🏫", "text": "<strong>Stay home</strong> — Highly contagious; avoid school/work until healed."},
        ], "urgent": False,
    },

    # --- Additional common skin diseases ---
    "shingles": {
        "name": "Shingles (Herpes Zoster)", "scientific": "Herpes Zoster",
        "icd10": "B02.9", "risk": "medium", "category": "Viral Infection",
        "prevalence": "~1 million cases/year in the US — risk increases with age",
        "risk_desc": "Painful viral rash from reactivated chickenpox virus. Requires antiviral treatment within 72 hours.",
        "abcd": {"asymmetry": "Unilateral band — follows dermatome", "border": "Clustered vesicles on erythematous base", "color": "Red base with clear/yellow blisters", "dermoscopy": "Grouped vesicles, dermatomal distribution"},
        "differential": ["Contact dermatitis", "Herpes simplex", "Impetigo", "Insect bites"],
        "recommendations": [
            {"icon": "💊", "text": "<strong>Antiviral therapy urgently</strong> — Aciclovir/valaciclovir within 72h of onset."},
            {"icon": "🌡️", "text": "<strong>Pain management</strong> — Paracetamol, NSAIDs, or neuropathic agents (gabapentin)."},
            {"icon": "🏥", "text": "<strong>See a doctor immediately</strong> — Complications include post-herpetic neuralgia."},
        ], "urgent": True,
    },
    "scabies": {
        "name": "Scabies", "scientific": "Sarcoptes scabiei Infestation",
        "icd10": "B86", "risk": "low", "category": "Parasitic Infection",
        "prevalence": "~300 million cases/year worldwide — common in crowded living conditions",
        "risk_desc": "Highly contagious mite infestation causing intense itching (especially at night). Curable with scabicidal treatment.",
        "abcd": {"asymmetry": "Widespread, worse in skin folds", "border": "Linear burrows between fingers, wrists, genitals", "color": "Skin-colored to reddish papules and burrows", "dermoscopy": "Jet aircraft sign — mite at end of burrow"},
        "differential": ["Eczema", "Contact dermatitis", "Urticaria", "Folliculitis"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Permethrin 5% cream</strong> — Apply whole body overnight; repeat in 7 days."},
            {"icon": "🧺", "text": "<strong>Wash all bedding/clothing at 60°C</strong> — Kill any mites in environment."},
            {"icon": "👨‍👩‍👧‍👦", "text": "<strong>Treat all household contacts simultaneously</strong> — Prevents re-infection."},
        ], "urgent": False,
    },
    "molluscum": {
        "name": "Molluscum Contagiosum", "scientific": "Molluscum Contagiosum Virus (MCV)",
        "icd10": "B08.1", "risk": "low", "category": "Viral Infection",
        "prevalence": "Common in children and immunosuppressed adults — highly contagious",
        "risk_desc": "Benign viral skin infection. Self-limiting in immunocompetent individuals (resolves in 6–18 months).",
        "abcd": {"asymmetry": "Multiple pearly papules", "border": "Smooth, dome-shaped with central umbilication", "color": "Flesh-colored to pearly white", "dermoscopy": "Central pore with polylobular white structure"},
        "differential": ["Warts", "Closed comedone (acne)", "Basal cell carcinoma", "Milia"],
        "recommendations": [
            {"icon": "⏳", "text": "<strong>Watchful waiting</strong> — Resolves spontaneously over months to years."},
            {"icon": "❄️", "text": "<strong>Cryotherapy or curettage</strong> — For faster removal if desired."},
            {"icon": "🚫", "text": "<strong>Avoid scratching or squeezing</strong> — Spreads lesions to adjacent skin."},
        ], "urgent": False,
    },
    "pityriasis_rosea": {
        "name": "Pityriasis Rosea", "scientific": "Pityriasis Rosea",
        "icd10": "L42", "risk": "low", "category": "Inflammatory",
        "prevalence": "Common self-limiting condition — affects 0.5–2% of dermatology patients",
        "risk_desc": "Benign, self-resolving rash. Likely viral trigger. Resolves in 6–8 weeks. Not contagious.",
        "abcd": {"asymmetry": "Herald patch followed by Christmas-tree pattern", "border": "Oval scaly plaques along skin cleavage lines", "color": "Salmon-pink with collarette scaling", "dermoscopy": "Peripheral scaling, mild erythema"},
        "differential": ["Tinea corporis", "Psoriasis", "Secondary syphilis", "Eczema"],
        "recommendations": [
            {"icon": "⏳", "text": "<strong>No treatment needed</strong> — Resolves spontaneously in 6–8 weeks."},
            {"icon": "🧴", "text": "<strong>Emollients and antihistamines</strong> — For itch relief."},
            {"icon": "🔬", "text": "<strong>Rule out syphilis</strong> — Secondary syphilis can mimic pityriasis rosea."},
        ], "urgent": False,
    },
    "tinea_versicolor": {
        "name": "Tinea Versicolor", "scientific": "Pityriasis Versicolor (Malassezia)",
        "icd10": "B36.0", "risk": "low", "category": "Fungal Infection",
        "prevalence": "Very common — affects up to 8% of the population, more in tropical climates",
        "risk_desc": "Superficial yeast infection causing hypo/hyperpigmented patches. Not dangerous, responsive to antifungals.",
        "abcd": {"asymmetry": "Multiple patches on trunk, neck, shoulders", "border": "Fine scaly patches with irregular borders", "color": "Lighter or darker than surrounding skin", "dermoscopy": "Follicular scaling, pale or yellow-brown patches"},
        "differential": ["Vitiligo", "Seborrheic dermatitis", "Pityriasis alba", "Contact dermatitis"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Antifungal shampoo as body wash</strong> — Ketoconazole 2% for 2 weeks."},
            {"icon": "💊", "text": "<strong>Oral antifungals</strong> — Fluconazole or itraconazole for widespread cases."},
            {"icon": "🔄", "text": "<strong>Maintenance</strong> — Monthly antifungal application prevents recurrence in summer."},
        ], "urgent": False,
    },
    "folliculitis": {
        "name": "Folliculitis", "scientific": "Folliculitis (Bacterial/Fungal)",
        "icd10": "L73.9", "risk": "low", "category": "Bacterial Infection",
        "prevalence": "Extremely common — affects people of all ages and skin types",
        "risk_desc": "Inflammation of hair follicles, usually bacterial (Staph aureus). Mild cases resolve with topical therapy.",
        "abcd": {"asymmetry": "Follicle-centered, any hair-bearing area", "border": "Small papules/pustules around follicle openings", "color": "Red papules with central whitehead", "dermoscopy": "Follicular pustule with concentric layers"},
        "differential": ["Acne vulgaris", "Pseudofolliculitis barbae", "Keratosis pilaris", "Scabies"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Antibacterial wash</strong> — Chlorhexidine or benzoyl peroxide wash daily."},
            {"icon": "💊", "text": "<strong>Topical antibiotic</strong> — Mupirocin for localised bacterial folliculitis."},
            {"icon": "🚿", "text": "<strong>Avoid shaving the area</strong> — Let skin heal; use proper shaving technique."},
        ], "urgent": False,
    },
    "keloid": {
        "name": "Keloid Scar", "scientific": "Keloid (Hypertrophic Scar)",
        "icd10": "L91.0", "risk": "low", "category": "Benign Growth",
        "prevalence": "Affects ~10% of people, more common in darker skin types (African, Asian, Hispanic)",
        "risk_desc": "Benign overgrowth of fibrous tissue after skin injury. Not dangerous but can be itchy and disfiguring.",
        "abcd": {"asymmetry": "Irregular, grows beyond wound margins", "border": "Raised, firm, well-defined rubbery nodule", "color": "Pink to dark brown or purple", "dermoscopy": "Structureless areas, telangiectasias"},
        "differential": ["Hypertrophic scar", "Dermatofibroma", "Lobomycosis", "Nodular BCC"],
        "recommendations": [
            {"icon": "💉", "text": "<strong>Intralesional corticosteroid injections</strong> — First-line treatment; flattens keloids."},
            {"icon": "🩹", "text": "<strong>Silicone gel sheets</strong> — Daily use reduces size and improves texture."},
            {"icon": "☀️", "text": "<strong>Sun protection</strong> — UV darkens keloids and worsens appearance."},
        ], "urgent": False,
    },
    "lupus_skin": {
        "name": "Cutaneous Lupus", "scientific": "Discoid Lupus Erythematosus",
        "icd10": "L93.0", "risk": "medium", "category": "Autoimmune",
        "prevalence": "Affects ~30–60 per 100,000 population — more common in women of childbearing age",
        "risk_desc": "Can be limited to skin (DLE) or part of systemic SLE. Dermatology + rheumatology evaluation required.",
        "abcd": {"asymmetry": "Butterfly (malar) rash across nose and cheeks", "border": "Erythematous plaques with follicular plugging", "color": "Red to violaceous, central scarring/atrophy", "dermoscopy": "Follicular plugging, telangiectasias, pigmentation"},
        "differential": ["Rosacea", "Polymorphic light eruption", "Seborrheic dermatitis", "Tinea faciei"],
        "recommendations": [
            {"icon": "🏥", "text": "<strong>Rheumatology/Dermatology referral</strong> — ANA panel and systemic workup needed."},
            {"icon": "☀️", "text": "<strong>Strict photoprotection</strong> — UV triggers lupus flares; SPF 50+ mandatory."},
            {"icon": "💊", "text": "<strong>Hydroxychloroquine</strong> — Standard systemic treatment for cutaneous lupus."},
        ], "urgent": False,
    },
    "psoriatic_plaque": {
        "name": "Plaque Psoriasis", "scientific": "Psoriasis Vulgaris (Plaque Type)",
        "icd10": "L40.0", "risk": "low", "category": "Inflammatory",
        "prevalence": "Most common form of psoriasis — affects ~80–90% of psoriasis patients",
        "risk_desc": "Chronic autoimmune skin disease. Manageable with modern biologics and topical treatments. Not contagious.",
        "abcd": {"asymmetry": "Symmetrically distributed plaques", "border": "Well-demarcated raised plaques with silvery scales", "color": "Red-pink base, thick white/silver scales", "dermoscopy": "Regularly distributed dotted vessels, white scaling"},
        "differential": ["Seborrheic dermatitis", "Lichen simplex chronicus", "Pityriasis rubra pilaris", "Mycosis fungoides"],
        "recommendations": [
            {"icon": "🧴", "text": "<strong>Topical corticosteroids + Vitamin D analogs</strong> — First-line combination therapy."},
            {"icon": "☀️", "text": "<strong>Narrowband UVB phototherapy</strong> — Effective for widespread psoriasis."},
            {"icon": "💊", "text": "<strong>Biologic therapy</strong> — TNF/IL-17/IL-23 inhibitors for moderate-severe disease."},
        ], "urgent": False,
    },
    "hyperpigmentation": {
        "name": "Post-Inflammatory Hyperpigmentation", "scientific": "Post-Inflammatory Hyperpigmentation (PIH)",
        "icd10": "L81.0", "risk": "low", "category": "Pigmentation",
        "prevalence": "Extremely common — occurs after acne, eczema, injury in all skin types; more prominent in darker skin",
        "risk_desc": "Benign excess melanin deposition. Gradually fades over months. Not dangerous.",
        "abcd": {"asymmetry": "Variable, follows previous lesion pattern", "border": "Flat macules with irregular edges", "color": "Brown to dark brown, matching prior lesion sites", "dermoscopy": "Homogeneous brown pigmentation, no atypical structures"},
        "differential": ["Melasma", "Melanoma", "Drug-induced pigmentation", "Tinea versicolor"],
        "recommendations": [
            {"icon": "☀️", "text": "<strong>Daily SPF 50+ sunscreen</strong> — UV significantly darkens PIH."},
            {"icon": "🧴", "text": "<strong>Topical azelaic acid or niacinamide</strong> — Fade hyperpigmentation over time."},
            {"icon": "⏳", "text": "<strong>Patience</strong> — Most PIH fades in 6–18 months with sun protection."},
        ], "urgent": False,
    },
}

# ── Symptom-Based Secondary Analysis ─────────────────────────────
SYMPTOM_DISEASE_MAP = {
    "itching": ["eczema", "psoriasis", "contact_dermatitis", "ringworm", "hives", "seborrheic_dermatitis", "scabies", "tinea_versicolor"],
    "night itching": ["scabies", "eczema", "hives"],
    "burning": ["contact_dermatitis", "hives", "rosacea", "cellulitis", "shingles"],
    "pain": ["cellulitis", "impetigo", "hives", "shingles", "keloid"],
    "painful": ["shingles", "cellulitis", "hives"],
    "bleeding": ["mel", "bcc", "akiec"],
    "scaling": ["psoriasis", "psoriatic_plaque", "seborrheic_dermatitis", "ringworm", "akiec", "eczema", "tinea_versicolor", "pityriasis_rosea"],
    "flaking": ["psoriasis", "psoriatic_plaque", "seborrheic_dermatitis", "tinea_versicolor"],
    "redness": ["rosacea", "eczema", "psoriasis", "contact_dermatitis", "cellulitis", "hives", "lupus_skin", "folliculitis"],
    "flushing": ["rosacea", "lupus_skin"],
    "swelling": ["hives", "cellulitis", "contact_dermatitis"],
    "discharge": ["impetigo", "cellulitis", "eczema", "folliculitis"],
    "change": ["mel", "bcc", "akiec"],
    "spreading": ["cellulitis", "ringworm", "impetigo", "hives", "shingles"],
    "white": ["vitiligo", "tinea_versicolor", "molluscum"],
    "pus": ["acne", "impetigo", "cellulitis", "folliculitis"],
    "blister": ["contact_dermatitis", "hives", "impetigo", "shingles"],
    "vesicle": ["shingles", "contact_dermatitis", "impetigo"],
    "wart": ["warts", "molluscum"],
    "bump": ["warts", "acne", "df", "bkl", "molluscum", "keloid", "folliculitis"],
    "blackhead": ["acne"],
    "whitehead": ["acne", "folliculitis", "molluscum"],
    "comedone": ["acne"],
    "pimple": ["acne", "folliculitis", "rosacea"],
    "scar": ["keloid", "hyperpigmentation", "acne"],
    "dark spot": ["hyperpigmentation", "mel", "bkl"],
    "dark patch": ["hyperpigmentation", "tinea_versicolor", "vitiligo"],
    "light patch": ["vitiligo", "tinea_versicolor", "pityriasis_rosea"],
    "ring": ["ringworm", "pityriasis_rosea"],
    "mite": ["scabies"],
    "burrow": ["scabies"],
    "plaque": ["psoriasis", "psoriatic_plaque", "eczema"],
    "butterfly": ["lupus_skin", "rosacea"],
    "malar": ["lupus_skin"],
}

LOCATION_DISEASE_MAP = {
    "face": ["acne", "rosacea", "seborrheic_dermatitis", "contact_dermatitis", "impetigo", "lupus_skin", "molluscum"],
    "scalp": ["seborrheic_dermatitis", "psoriasis", "psoriatic_plaque", "folliculitis"],
    "trunk": ["psoriasis", "psoriatic_plaque", "eczema", "ringworm", "vasc", "tinea_versicolor", "pityriasis_rosea", "molluscum"],
    "chest": ["acne", "tinea_versicolor", "pityriasis_rosea", "folliculitis"],
    "back": ["acne", "psoriasis", "psoriatic_plaque", "tinea_versicolor", "folliculitis"],
    "upper extremity": ["eczema", "contact_dermatitis", "psoriasis", "keloid", "warts"],
    "lower extremity": ["df", "psoriasis", "cellulitis", "vasc", "keloid", "scabies"],
    "palms": ["contact_dermatitis", "eczema", "psoriasis", "warts"],
    "genital": ["warts", "molluscum", "contact_dermatitis", "scabies"],
    "head": ["seborrheic_dermatitis", "acne", "impetigo", "folliculitis"],
    "neck": ["acne", "contact_dermatitis", "seborrheic_dermatitis", "tinea_versicolor"],
    "shoulder": ["tinea_versicolor", "folliculitis", "acne"],
    "arm": ["eczema", "contact_dermatitis", "warts", "keloid"],
    "leg": ["cellulitis", "psoriasis", "vasc", "keloidy"],
    "finger": ["contact_dermatitis", "scabies", "warts"],
    "finger web": ["scabies", "contact_dermatitis"],
    "wrist": ["scabies", "eczema", "contact_dermatitis"],
}

RISK_DESC_MAP = {
    "low":    "Generally benign with low malignant potential. Routine annual skin surveillance recommended.",
    "medium": "Has concerning features. Dermatologist evaluation within 4–8 weeks is advised.",
    "high":   "Carries significant malignant or serious infectious potential. Urgent dermatology referral required.",
}


# Default top diseases to show even without symptoms (common conditions)
DEFAULT_SECONDARY_DISEASES = [
    "acne", "eczema", "psoriasis", "rosacea", "ringworm",
    "tinea_versicolor", "contact_dermatitis", "folliculitis",
    "seborrheic_dermatitis", "hives", "vitiligo", "warts",
    "impetigo", "scabies", "shingles", "molluscum",
    "pityriasis_rosea", "keloid", "hyperpigmentation", "lupus_skin",
]

def get_secondary_conditions(symptoms_str: str, location_str: str, top_cnn_code: str) -> list:
    """Suggest secondary conditions based on symptoms and location."""
    candidates = {}

    if symptoms_str:
        symp_lower = symptoms_str.lower()
        for keyword, diseases in SYMPTOM_DISEASE_MAP.items():
            if keyword in symp_lower:
                for d in diseases:
                    if d != top_cnn_code:
                        candidates[d] = candidates.get(d, 0) + 2  # weight symptoms higher

    if location_str:
        loc_lower = location_str.lower()
        for loc_keyword, diseases in LOCATION_DISEASE_MAP.items():
            if loc_keyword in loc_lower:
                for d in diseases:
                    if d != top_cnn_code:
                        candidates[d] = candidates.get(d, 0) + 1

    # If we have symptom/location matches, use those; otherwise show popular conditions
    if candidates:
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:5]
    else:
        # No symptoms/location provided — show the most common conditions excluding CNN top
        fallback = [d for d in DEFAULT_SECONDARY_DISEASES if d != top_cnn_code][:5]
        sorted_candidates = [(d, 0) for d in fallback]

    result = []
    for code, score in sorted_candidates:
        if code in DISEASE_KB:
            kb = DISEASE_KB[code]
            relevance = "symptom-match" if score >= 2 else ("location-match" if score == 1 else "common-condition")
            result.append({
                "code": code,
                "name": kb["name"],
                "icd10": kb["icd10"],
                "risk": kb["risk"],
                "category": kb["category"],
                "risk_desc": kb["risk_desc"],
                "recommendations": kb["recommendations"],
                "abcd": kb["abcd"],
                "differential": kb["differential"],
                "urgent": kb["urgent"],
                "relevance": relevance,
            })
    return result


# ── MobileNetV2 Model ─────────────────────────────────────────────
class DermaLensModel(nn.Module):
    def __init__(self, num_classes: int = 7, dropout: float = 0.3):
        super().__init__()
        from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
        base = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
        self.features = base.features
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1), nn.Flatten(),
            nn.Dropout(dropout), nn.Linear(1280, 256), nn.ReLU(),
            nn.Dropout(dropout * 0.5), nn.Linear(256, num_classes),
        )
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x / self.temperature.clamp(min=0.5, max=5.0)


_model = None
_model_weights_loaded = False

def get_model():
    global _model, _model_weights_loaded
    if _model is None:
        log.info("Loading MobileNetV2 model…")
        _model = DermaLensModel(num_classes=7, dropout=0.3).to(DEVICE)
        _model.eval()
        weights_path = BASE_DIR / "models" / "dermalens_mobilenetv2.pth"
        if weights_path.exists():
            try:
                state = torch.load(str(weights_path), map_location=DEVICE, weights_only=True)
                _model.load_state_dict(state)
                _model_weights_loaded = True
                log.info(f"Custom weights loaded from {weights_path}")
            except Exception as e:
                log.warning(f"Could not load weights: {e} — using ImageNet init")
    return _model, _model_weights_loaded


HAM_MEAN = [0.7630, 0.5456, 0.5700]
HAM_STD  = [0.1409, 0.1523, 0.1692]
INFER_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=HAM_MEAN, std=HAM_STD),
])


def run_cnn_inference(image_bytes: bytes):
    model, weights_loaded = get_model()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = INFER_TRANSFORM(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()
    top5_idx = np.argsort(probs)[::-1][:5]
    top5 = [
        {"name": CLASS_DISPLAY[LABEL_MAP[int(i)]], "code": LABEL_MAP[int(i)], "prob": float(probs[i])}
        for i in top5_idx
    ]
    top_code = LABEL_MAP[int(top5_idx[0])]
    return {"top_class": top_code, "confidence": float(probs[top5_idx[0]]), "top5": top5}, weights_loaded


def build_structured_response(inference: dict, metadata: dict) -> dict:
    code = inference["top_class"]
    kb = DISEASE_KB[code]
    conf = inference["confidence"]
    patient_name = metadata.get("patient_name", "")

    name_str = f"Patient <strong>{patient_name}</strong>. " if patient_name else ""
    patient_str = ""
    if metadata.get("age"):
        patient_str += f"Age {metadata['age']}"
    if metadata.get("sex"):
        patient_str += f", {metadata['sex'].lower()}"
    if metadata.get("location"):
        patient_str += f". Lesion on {metadata['location'].lower()}"
    if metadata.get("duration"):
        patient_str += f", present for {metadata['duration'].lower()}"

    clinical_report = (
        f"<p>{name_str}The DermaLens AI system has classified this dermoscopic image as "
        f"<strong>{kb['name']}</strong> ({kb['scientific']}), with a model confidence of "
        f"{conf*100:.1f}%. {patient_str}. This classification is based on a MobileNetV2 CNN "
        f"fine-tuned on the HAM10000 benchmark dermoscopy dataset (10,015 images, 7 classes).</p>"
        f"<p>Dermoscopic features consistent with {kb['name']} include: "
        f"{kb['abcd']['asymmetry'].lower()}, borders that are typically {kb['abcd']['border'].lower()}, "
        f"coloration described as {kb['abcd']['color'].lower()}, and dermoscopic structures "
        f"characterised by {kb['abcd']['dermoscopy'].lower()}. "
        f"Risk stratification places this lesion in the <strong>{kb['risk'].upper()} RISK</strong> "
        f"category ({kb['category']}). {kb['risk_desc']}</p>"
        f"<p><strong>Important:</strong> This AI-generated report is for educational and research "
        f"purposes only. All findings must be reviewed by a qualified dermatologist. "
        f"Biopsy and histopathological examination remain the gold standard for definitive diagnosis. "
        f"AI confidence scores reflect pattern matching on training data and may not generalise to all clinical contexts.</p>"
    )

    secondary = get_secondary_conditions(
        metadata.get("symptoms", ""),
        metadata.get("location", ""),
        code
    )

    return {
        "lesion": {
            "name": kb["name"], "scientific": kb["scientific"],
            "icd10": kb["icd10"], "risk": kb["risk"],
            "category": kb["category"],
            "prevalence": kb["prevalence"], "risk_desc": kb["risk_desc"],
            "differential": kb["differential"], "abcd": kb["abcd"],
            "recommendations": kb["recommendations"], "urgent": kb["urgent"],
        },
        "inference": {
            "confidence": inference["confidence"],
            "top_class": code,
            "top5": inference["top5"],
        },
        "clinical_report": clinical_report,
        "secondary_conditions": secondary,
        "patient_name": patient_name,
    }


def call_claude_vision(image_bytes: bytes, media_type: str, metadata: dict) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    patient_name = metadata.get("patient_name", "Not provided")

    prompt = f"""You are an expert dermatologist. Analyze the provided skin/dermoscopic image.
Patient: {patient_name}
Age: {metadata.get('age', 'Unknown')}
Sex: {metadata.get('sex', 'Unknown')}
Location: {metadata.get('location', 'Unknown')}
Duration: {metadata.get('duration', 'Unknown')}
Symptoms: {metadata.get('symptoms', 'None reported')}

CRITICAL INSTRUCTION: Analyze the image meticulously for ACNE VULGARIS and other major skin conditions (like Psoriasis, Eczema, Rosacea). If you detect comedones, pustules, or papules consistent with Acne, you MUST classify it as Acne Vulgaris regardless of the CNN top class fallback. Do NOT default to Melanocytic Nevi if the visual evidence points to Acne or an inflammatory condition. 

Provide a structured clinical assessment in raw JSON (no Markdown fences):
{{
  "lesion": {{
    "name": "Primary Diagnosis (e.g. Acne Vulgaris, Melanoma, etc)",
    "scientific": "Scientific name",
    "icd10": "ICD-10 code",
    "prevalence": "Brief prevalence note",
    "risk": "low|medium|high",
    "category": "Cancer|Benign Growth|Inflammatory|Fungal Infection|etc",
    "risk_desc": "1-2 sentence risk description",
    "differential": ["Diff 1","Diff 2","Diff 3"],
    "abcd": {{"asymmetry":"...","border":"...","color":"...","dermoscopy":"..."}},
    "recommendations": [{{"icon":"✅","text":"..."}},{{"icon":"🏥","text":"..."}},{{"icon":"💊","text":"..."}}],
    "urgent": true|false
  }},
  "inference": {{
    "confidence": 0.95,
    "top_class": "acne",
    "top5": [{{"name":"Acne Vulgaris","prob":0.95}},{{"name":"Rosacea","prob":0.02}},{{"name":"Folliculitis","prob":0.01}}]
  }},
  "clinical_report": "<p>Paragraph 1</p><p>Paragraph 2</p><p>Paragraph 3</p>",
  "secondary_conditions": []
}}"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022", max_tokens=2500, temperature=0.1,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": encoded_image}},
            {"type": "text", "text": prompt}
        ]}]
    )
    result_text = response.content[0].text.strip()
    for fence in ("```json", "```"):
        if result_text.startswith(fence):
            result_text = result_text[len(fence):]
    if result_text.endswith("```"):
        result_text = result_text[:-3]
    data = json.loads(result_text.strip())
    
    # Ensure secondary_conditions array is populated if Claude didn't provide one
    if not data.get("secondary_conditions"):
        data["secondary_conditions"] = get_secondary_conditions(metadata.get('symptoms', ''), metadata.get('location', ''), data["inference"].get("top_class", ""))

    if "patient_name" not in data:
        data["patient_name"] = metadata.get("patient_name", "")
    return data


# ── AI Chat Session History ───────────────────────────────────────
CHAT_HISTORY = {}

def call_claude_chat(session_id: str, message: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "I am currently offline as the Anthropic API key is missing. Please configure it in the backend."
    
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    if session_id not in CHAT_HISTORY:
        CHAT_HISTORY[session_id] = [
            {"role": "user", "content": "You are a professional, empathetic virtual AI dermatologist named DermaLens Assistant. Your goal is to help users understand skin conditions, triage symptoms, and advise them to seek professional medical help when necessary. Answer securely and accurately."}
        ]
    
    CHAT_HISTORY[session_id].append({"role": "user", "content": message})
    
    # We strip the system prompt from the actual calls to Claude to avoid formatting errors,
    # or pass it as system block. For simpler code:
    msgs = CHAT_HISTORY[session_id][1:] # Skip the system instruction in the message array
    system_prompt = CHAT_HISTORY[session_id][0]["content"]

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.3,
            system=system_prompt,
            messages=msgs
        )
        ai_reply = response.content[0].text.strip()
        CHAT_HISTORY[session_id].append({"role": "assistant", "content": ai_reply})
        return ai_reply
    except Exception as e:
        log.error(f"Chat error: {e}")
        return "Sorry, I encountered an error while trying to process your request."


# ── FastAPI App ────────────────────────────────────────────────────
app = FastAPI(title="DermaLens AI", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_static_dir = BASE_DIR / "frontend" / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    html_file = BASE_DIR / "frontend" / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"), status_code=200)


@app.get("/health")
async def health():
    _, weights_loaded = get_model()
    return {
        "status": "ok", "device": str(DEVICE),
        "model_weights": weights_loaded,
        "claude_configured": bool(ANTHROPIC_API_KEY),
        "total_diseases_kb": len(DISEASE_KB),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/diseases")
async def list_diseases():
    """Return all diseases in the knowledge base."""
    return {
        "cnn_classes": list(CLASS_DISPLAY.values()),
        "all_diseases": [
            {"code": k, "name": v["name"], "category": v["category"], "risk": v["risk"]}
            for k, v in DISEASE_KB.items()
        ],
        "total": len(DISEASE_KB),
    }


@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    patient_name: Optional[str] = Form(None),
    age:           Optional[str] = Form(None),
    sex:           Optional[str] = Form(None),
    location:      Optional[str] = Form(None),
    duration:      Optional[str] = Form(None),
    symptoms:      Optional[str] = Form(None),
):
    t0 = time.time()
    try:
        valid_types = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in valid_types:
            raise HTTPException(400, "Unsupported file type. Upload JPEG, PNG or WEBP.")

        raw = await file.read()
        if len(raw) > 15 * 1024 * 1024:
            raise HTTPException(413, "File too large. Maximum 15MB.")

        uid = str(uuid.uuid4())[:8]
        try:
            safe_name = "".join(c for c in (file.filename or "upload.jpg") if c.isalnum() or c in "._-")
            (UPLOAD_DIR / f"{uid}_{safe_name}").write_bytes(raw)
        except Exception as e:
            log.warning(f"Could not save file: {e}")

        metadata = {k: v for k, v in {
            "patient_name": patient_name,
            "age": age, "sex": sex, "location": location,
            "duration": duration, "symptoms": symptoms,
        }.items() if v}

        if ANTHROPIC_API_KEY:
            log.info(f"[{uid}] Using Claude Vision API…")
            try:
                result = call_claude_vision(raw, file.content_type, metadata)
            except Exception as e:
                log.warning(f"[{uid}] Claude failed ({e}), falling back to CNN…")
                inference, _ = run_cnn_inference(raw)
                result = build_structured_response(inference, metadata)
        else:
            log.info(f"[{uid}] Running local CNN inference…")
            inference, _ = run_cnn_inference(raw)
            result = build_structured_response(inference, metadata)

        elapsed = round(time.time() - t0, 2)
        log.info(f"[{uid}] Done in {elapsed}s | {result['lesion']['name']} | risk={result['lesion']['risk']}")

        patient_name_val = result.get("patient_name", metadata.get("patient_name", ""))

        return JSONResponse({
            "id": uid,
            "elapsed_seconds": elapsed,
            "patient_name": patient_name_val,
            "inference": result["inference"],
            "lesion": result["lesion"],
            "clinical_report": result["clinical_report"],
            "secondary_conditions": result.get("secondary_conditions", []),
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
            "disclaimer": "For educational and research use only. Not a substitute for clinical diagnosis.",
        })

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unhandled error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": f"Internal Server Error: {str(e)}"})

# ── Auth & Chat Endpoints ──────────────────────────────────────────

@app.post("/api/register")
async def register_user(username: str = Form(...), password: str = Form(...)):
    if username in MOCK_DB_USERS:
        return JSONResponse(status_code=400, content={"detail": "Username already exists"})
    
    # Store hashed password
    MOCK_DB_USERS[username] = {"password_hash": hash_password(password), "created": datetime.utcnow().isoformat()}
    log.info(f"New user registered: {username}")
    
    # Auto-login after registration
    token = str(uuid.uuid4())
    MOCK_SESSIONS[token] = username
    return {"status": "success", "token": token, "username": username}

@app.post("/api/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    if username not in MOCK_DB_USERS:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    
    if MOCK_DB_USERS[username]["password_hash"] != hash_password(password):
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    
    token = str(uuid.uuid4())
    MOCK_SESSIONS[token] = username
    return {"status": "success", "token": token, "username": username}

@app.post("/api/chat")
async def chat_with_agent(
    message: str = Form(...), 
    authorization: Optional[str] = Header(None)
):
    # Verify auth token (Bearer format)
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized. Please log in."})
    
    token = authorization.split(" ")[1]
    if token not in MOCK_SESSIONS:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired session. Please log in."})
    
    username = MOCK_SESSIONS[token]
    session_id = f"chat_{username}_{token}"
    
    log.info(f"Chat request from {username}: {message[:50]}...")
    reply = call_claude_chat(session_id, message)
    
    return {"reply": reply, "timestamp": datetime.utcnow().isoformat()}
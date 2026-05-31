# DermaLens AI 🔬

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Anthropic-7B2FBE?style=for-the-badge&logo=anthropic&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

### CNN (MobileNetV2 / HAM10000) + Claude AI Skin Lesion Analysis System

A full-stack, production-ready dermoscopic analysis system combining a fine-tuned deep learning classifier with a large language model for clinical report generation.

**⚠️ For educational and research purposes only — not a medical device.**

</div>

---

## ✨ Features

- 🧠 **MobileNetV2 CNN** fine-tuned on HAM10000 (10,015 dermoscopy images, 7 classes)
- 🤖 **Claude AI** generates structured clinical reports from CNN predictions
- 📊 **25+ skin condition knowledge base** with ABCD criteria, ICD-10 codes, differential diagnoses
- 🎯 **Symptom + location aware** secondary condition suggestions
- 🖥️ **Single-file SPA frontend** — zero build step, pure HTML/CSS/JS
- 🔐 **Session authentication** with in-memory store (prototype)
- 🐳 **Docker-ready** — one command deploy
- 📈 **Temperature calibration** for well-calibrated confidence scores

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                              │
│  Drag & Drop Upload  ─►  REST API Call  ─►  Render Report  │
└─────────────────────────┬───────────────────────────────────┘
                          │ POST /api/analyze (multipart/form-data)
┌─────────────────────────▼───────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  Image Upload   │    │   Clinical Report Generator  │   │
│  │  & Validation   │    │   (Anthropic Claude API)     │   │
│  └────────┬────────┘    └──────────────┬───────────────┘   │
│           │                            │                    │
│  ┌────────▼────────────────────────────▼───────────────┐   │
│  │              MobileNetV2 Classifier                 │   │
│  │    HAM10000-trained · Temperature Calibrated        │   │
│  │    7-class Softmax · Focal Loss · 224×224 input     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
dermalens-ai/                    ← GitHub repo root
├── backend/
│   └── main.py                  ← FastAPI app: CNN inference, Claude API, auth, knowledge base
├── frontend/
│   └── index.html               ← Single-page application (HTML/CSS/JS — no build step)
├── data/
│   └── .gitkeep                 ← Place HAM10000 dataset here (downloaded separately)
├── models/
│   └── .gitkeep                 ← Trained weights placed here after train.py
├── uploads/
│   └── .gitkeep                 ← Runtime uploads (auto-created, git-ignored)
├── logs/
│   └── .gitkeep                 ← App logs (auto-created, git-ignored)
├── train.py                     ← HAM10000 MobileNetV2 training script
├── diagnose.py                  ← Standalone diagnosis / health check utility
├── download_dataset.py          ← Helper to download HAM10000 via Kaggle API
├── requirements.txt             ← Python dependencies
├── Dockerfile                   ← Docker image definition
├── docker-compose.yml           ← Docker Compose config
├── .env.example                 ← Environment variable template
├── .gitignore
├── .gitattributes
├── LICENSE
└── README.md
```

---

## 📊 HAM10000 Dataset

The model is trained on the **HAM10000** dataset — a large collection of multi-source dermatoscopic images of common pigmented skin lesions.

| Code     | Class                       | Risk      | ICD-10 | ~Count |
|----------|-----------------------------|-----------|--------|--------|
| `nv`     | Melanocytic Nevi            | 🟢 Low    | D22.9  | 6,705  |
| `mel`    | Melanoma                    | 🔴 High   | C43.9  | 1,113  |
| `bkl`    | Benign Keratosis            | 🟢 Low    | L82.1  | 1,099  |
| `bcc`    | Basal Cell Carcinoma        | 🔴 High   | C44.91 | 514    |
| `akiec`  | Actinic Keratosis / Bowen's | 🟡 Medium | L57.0  | 327    |
| `vasc`   | Vascular Lesion             | 🟢 Low    | D18.01 | 142    |
| `df`     | Dermatofibroma              | 🟢 Low    | D23.9  | 115    |

> **Note:** Dataset is class-imbalanced. Training uses **WeightedRandomSampler** + **Focal Loss (γ=2.0)** to address this.

### Download Dataset

```bash
# Option A: Kaggle CLI (recommended)
pip install kaggle
kaggle datasets download -d kmader/skin-lesion-analysis-toward-melanoma-detection
unzip skin-lesion-analysis-toward-melanoma-detection.zip -d data/HAM10000

# Option B: Automated helper script
python download_dataset.py

# Option C: Harvard Dataverse (official)
# https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T
```

Expected structure after download:
```
data/HAM10000/
├── HAM10000_metadata.csv
├── HAM10000_images_part1/
│   ├── ISIC_0024306.jpg
│   └── ...
└── HAM10000_images_part2/
    └── ...
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key → [console.anthropic.com](https://console.anthropic.com)
- (Optional) CUDA GPU for training

### Option A — Local (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
copy .env.example .env
# Open .env and set: ANTHROPIC_API_KEY=sk-ant-...

# 5. Start the server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Open browser → http://localhost:8000
```

### Option B — Docker

```bash
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai

copy .env.example .env
# Edit .env: ANTHROPIC_API_KEY=sk-ant-...

docker-compose up --build
# → http://localhost:8000
```

### Option C — Windows One-Click

```
Double-click RUN_DERMALENS.bat
```

---

## 🧠 Model Training

### Step 1 — Download HAM10000 (see above)

### Step 2 — Train

```bash
# Standard (CPU)
python train.py --data_dir data/HAM10000 --epochs 30 --batch_size 32

# GPU (recommended)
python train.py --data_dir data/HAM10000 --epochs 50 --batch_size 64 --num_workers 4
```

| Argument        | Default | Description                        |
|-----------------|---------|------------------------------------|
| `--data_dir`    | —       | Path to HAM10000 (**required**)    |
| `--epochs`      | `30`    | Max training epochs                |
| `--batch_size`  | `32`    | Batch size (64 for GPU)            |
| `--lr`          | `0.001` | Base learning rate                 |
| `--patience`    | `8`     | Early stopping patience            |
| `--num_workers` | `4`     | DataLoader workers                 |

### Training Outputs → `models/`

| File                        | Description                              |
|-----------------------------|------------------------------------------|
| `dermalens_mobilenetv2.pth` | Best model weights (by val accuracy)     |
| `confusion_matrix.png`      | Per-class confusion matrix heatmap       |
| `training_curves.png`       | Loss & accuracy curves (train vs val)    |
| `training_history.json`     | Full epoch-by-epoch metrics as JSON      |

---

## 📈 Expected Model Performance

| Metric            | Value          |
|-------------------|----------------|
| Overall Accuracy  | **~82–86%**    |
| Balanced Accuracy | **~74–80%**    |
| Melanoma AUC      | **~0.90–0.93** |
| BCC AUC           | **~0.92–0.95** |

---

## 🧪 Training Details

| Component       | Choice                                             |
|-----------------|----------------------------------------------------|
| Backbone        | MobileNetV2 (ImageNet pre-trained)                |
| Fine-tuning     | Last 3 blocks + classifier head                   |
| Loss            | Focal Loss (γ=2.0) + inverse class weights        |
| Sampler         | WeightedRandomSampler                             |
| Optimizer       | AdamW with layer-wise LR                          |
| Scheduler       | CosineAnnealingWarmRestarts (T₀=10)               |
| Augmentation    | Flip, rotation ±30°, color jitter, random erasing |
| Calibration     | Temperature scaling (T=1.5, learnable)            |
| Input           | 224×224, HAM10000 channel statistics normalized   |
| Split           | 80% train / 10% val / 10% test (stratified)       |

---

## 🌐 API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint          | Description                           |
|--------|-------------------|---------------------------------------|
| POST   | `/api/analyze`    | Analyze image, return clinical report |
| GET    | `/health`         | Backend health + model status         |
| GET    | `/api/classes`    | All 7 HAM10000 class metadata         |
| GET    | `/api/model-info` | Model architecture + param count      |
| POST   | `/api/register`   | Register user (prototype)             |
| POST   | `/api/login`      | Login / get session token             |
| POST   | `/api/logout`     | Logout session                        |

### `POST /api/analyze` Request Fields

| Field          | Type   | Required | Description                   |
|----------------|--------|----------|-------------------------------|
| `file`         | image  | ✅       | JPEG/PNG/WEBP ≤ 15 MB         |
| `patient_name` | string | ❌       | Name for report header        |
| `age`          | string | ❌       | Patient age                   |
| `sex`          | string | ❌       | Biological sex                |
| `location`     | string | ❌       | Anatomic site of lesion       |
| `duration`     | string | ❌       | How long lesion present       |
| `symptoms`     | string | ❌       | Symptoms (itching, pain, etc.)|

---

## ⚙️ Environment Variables

| Variable           | Required | Description                        |
|--------------------|----------|------------------------------------|
| `ANTHROPIC_API_KEY`| ✅       | Your Anthropic Claude API key      |
| `PORT`             | ❌       | Server port (default: `8000`)      |
| `LOG_LEVEL`        | ❌       | Logging level (default: `info`)    |

> **No API key?** The system runs in **demo mode** — CNN inference, ABCD analysis, and all recommendations still work. Only Claude-generated reports are replaced with rule-based summaries.

---

## 🩺 Disease Knowledge Base (25+ Conditions)

| Category        | Conditions                                                     |
|-----------------|----------------------------------------------------------------|
| **CNN Classes** | Melanocytic Nevi, Melanoma, Benign Keratosis, BCC, AK, Vascular, Dermatofibroma |
| **Inflammatory**| Psoriasis, Eczema, Rosacea, Contact Dermatitis, Seborrheic Dermatitis, Folliculitis, Pityriasis Rosea |
| **Infections**  | Ringworm, Impetigo, Cellulitis, Shingles, Scabies, Molluscum Contagiosum, Warts |
| **Fungal**      | Tinea Versicolor                                              |
| **Pigmentation**| Vitiligo, Post-Inflammatory Hyperpigmentation                 |
| **Autoimmune**  | Cutaneous Lupus (DLE)                                         |
| **Allergic**    | Urticaria (Hives), Acne Vulgaris                              |
| **Scars**       | Keloid / Hypertrophic Scar                                    |

---

## ⚠️ Disclaimer

**This system is strictly for educational and research purposes only.**

- ❌ Not approved by the FDA or any regulatory body
- ❌ Not a substitute for clinical examination by a qualified dermatologist  
- ❌ Do not make clinical decisions based solely on AI output
- ✅ All findings must be confirmed by a licensed healthcare professional

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.

Dataset citation:
> Tschandl P., Rosendahl C., Kittler H. *The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions.* Sci. Data 5, 180161 (2018). [DOI: 10.1038/sdata.2018.161](https://doi.org/10.1038/sdata.2018.161)

---

## 🙏 Acknowledgements

- **HAM10000 Dataset** — Tschandl et al. (2018), Harvard Dataverse / ISIC Archive
- **MobileNetV2** — Sandler et al. (2018), Google Research
- **Anthropic Claude** — Clinical language model capabilities
- **FastAPI** — High-performance Python async web framework

---

<div align="center">
Made with ❤️ for the open-source dermatology AI community
</div>

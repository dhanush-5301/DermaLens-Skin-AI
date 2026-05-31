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

[![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/dermalens-ai?style=social)](https://github.com/YOUR_USERNAME/dermalens-ai)
[![Fork](https://img.shields.io/github/forks/YOUR_USERNAME/dermalens-ai?style=social)](https://github.com/YOUR_USERNAME/dermalens-ai/fork)

</div>

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation & Usage](#-installation--usage)
- [API Reference](#-api-reference)
- [Model Training](#-model-training)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#%EF%B8%8F-disclaimer)

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

## 🎯 Usage Examples

### 1. Drag & Drop Analysis
1. Upload a dermoscopic image via the web interface
2. Enter optional patient information (age, location, symptoms)
3. Click **Analyze** and wait for results (5-10 seconds)
4. View detailed clinical report with:
   - Primary diagnosis with confidence score
   - ABCD criteria analysis
   - ICD-10 codes and risk assessment
   - Differential diagnoses
   - Clinical recommendations

### 2. Programmatic API Usage

```python
import requests

# Prepare image and metadata
with open("lesion.jpg", "rb") as f:
    files = {"file": f}
    data = {
        "patient_name": "John Doe",
        "age": "45",
        "sex": "M",
        "location": "left shoulder",
        "symptoms": "itching, gradual growth",
    }
    
    response = requests.post(
        "http://localhost:8000/api/analyze",
        files=files,
        data=data
    )
    
    report = response.json()
    print(report["clinical_report"])
```

### 3. Batch Processing

```bash
# Analyze all images in a folder
for image in uploads/*.jpg; do
    python diagnose.py --image "$image" --output results/
done
```

---

## 🚀 Installation & Usage

### Prerequisites
- **Python 3.11+**
- **Anthropic API key** → [Get it here](https://console.anthropic.com/keys)
- **GPU (NVIDIA/CUDA)** — Optional, but recommended for training

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Key

```bash
# Copy example environment file
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=sk-ant-...
```

### Step 5: Run Application

**Option A — Local Development:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
# Open: http://localhost:8000
```

**Option B — Docker Compose:**
```bash
docker-compose up --build
# Open: http://localhost:8000
```

**Option C — Windows Batch File:**
```bash
RUN_DERMALENS.bat
```

---

## 📊 Expected Output

### Clinical Report Example

```
PATIENT INFORMATION
─────────────────────────────────────────
Name: John Doe
Age: 45 years
Location: Left shoulder
Duration: 3 months, gradual growth
Symptoms: Itching, occasional bleeding

PRIMARY DIAGNOSIS
─────────────────────────────────────────
Classification: Melanoma (Malignant)
Confidence: 87.3%
ICD-10: C43.9

ABCD CRITERIA ANALYSIS
─────────────────────────────────────────
Asymmetry: High (4/5)
Border Irregularity: High (4/5)
Color Variation: Present (brown, black)
Diameter: 12mm (>6mm threshold)
Overall Risk: HIGH - Recommend urgent referral

DIFFERENTIAL DIAGNOSES
─────────────────────────────────────────
1. Melanoma (87.3%) - MOST LIKELY
2. Dysplastic Nevus (9.5%)
3. Seborrheic Keratosis (2.2%)

CLINICAL RECOMMENDATIONS
─────────────────────────────────────────
⚠️ URGENT: Refer to dermatologist immediately
- Consider dermoscopy by specialist
- Possible biopsy recommended
- Document images for follow-up

SECONDARY CONDITIONS
─────────────────────────────────────────
Based on location and symptoms:
- Solar Lentigines (photodamage): 40% probability
- Actinic Keratosis: 15% probability
```

---

## 🔬 Troubleshooting

### Issue: ModuleNotFoundError: No module named 'torch'

**Solution:**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Anthropic API key not working

**Solution:**
1. Verify `.env` file exists in project root
2. Check that `ANTHROPIC_API_KEY=sk-ant-...` is set correctly
3. Test key at [console.anthropic.com](https://console.anthropic.com)

### Issue: "CUDA out of memory"

**Solution:**
```bash
# Reduce batch size
python train.py --data_dir data/HAM10000 --batch_size 16
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use different port
uvicorn backend.main:app --port 8001
```

For more troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🎓 Future Improvements

- [ ] **Multi-modal Input** — Add text-based history + image analysis combination
- [ ] **Mobile App** — React Native / Flutter app for iOS & Android
- [ ] **Real-time Webcam** — Live lesion analysis directly from camera
- [ ] **Patient Dashboard** — Track lesion history and follow-ups
- [ ] **Model Updates** — Vision Transformers (ViT) baseline comparison
- [ ] **Dataset Expansion** — Integrate additional dermoscopy datasets
- [ ] **Offline Mode** — Quantized model for edge deployment
- [ ] **Multi-language** — i18n support for global accessibility
- [ ] **Audit Logging** — Compliance with HIPAA/GDPR requirements
- [ ] **Explainability** — LIME/SHAP visualizations for model decisions
- [ ] **Batch API** — Async queue for bulk analysis
- [ ] **ML Monitoring** — Data drift detection and model retraining pipeline

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** this repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Commit your changes**: `git commit -am 'Add your feature description'`
4. **Push to branch**: `git push origin feature/your-feature-name`
5. **Submit a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guidelines for Python code
- Add docstrings to all functions
- Include unit tests for new features
- Update README.md if adding new functionality
- Ensure all tests pass: `pytest`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📝 Commit Message Standards

Please use clear, semantic commit messages:

❌ **Bad:**
```
update
fix
final
```

✅ **Good:**
```
Add user authentication endpoint
Fix image preprocessing color space bug
Improve model inference speed by 20%
Refactor API error handling
Update dataset documentation
```

---

## 📄 Disclaimer

**This system is strictly for educational and research purposes only.**

- ❌ Not approved by the FDA or any regulatory body
- ❌ Not a substitute for clinical examination by a qualified dermatologist  
- ❌ Do not make clinical decisions based solely on AI output
- ✅ All findings must be confirmed by a licensed healthcare professional

**Medical Disclaimer:** Always consult a qualified healthcare professional for any skin concerns. This software is provided "as-is" without any warranty of accuracy or fitness for medical use.

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for full details.

You are free to:
- ✅ Use this software commercially or privately
- ✅ Modify and distribute the code
- ✅ Include in proprietary applications

With the condition:
- ⚠️ Include the original license and copyright notice

### Dataset Citation

If you use the HAM10000 dataset in your research, please cite:

```bibtex
@article{tschandl2018ham10000,
  title={The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions},
  author={Tschandl, Philipp and Rosendahl, Cliff and Kittler, Harald},
  journal={Scientific Data},
  volume={5},
  pages={180161},
  year={2018},
  doi={10.1038/sdata.2018.161}
}
```

---

## 👥 Author & Contributors

**Created by:** Your Name / Your Organization

**Major Contributors:**
- Your Name — Core architecture & development
- Contributor Name — Dataset & training pipeline
- Contributor Name — Frontend UI/UX

Interested in contributing? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📞 Support & Contact

- **Issues & Bug Reports:** [GitHub Issues](https://github.com/YOUR_USERNAME/dermalens-ai/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/dermalens-ai/discussions)
- **Email:** your-email@example.com

---

## 🙏 Acknowledgements

This project was made possible by:

- **HAM10000 Dataset** — Tschandl et al. (2018), Harvard Dataverse / ISIC Archive
- **MobileNetV2** — Sandler et al. (2018), Google Research
- **Anthropic Claude** — Advanced clinical language model capabilities
- **FastAPI** — Modern, high-performance Python async web framework
- **PyTorch** — Flexible deep learning framework
- **Open Source Community** — Countless libraries and tools

---

## 📊 Project Statistics

- **Lines of Code:** ~2000+
- **Python Modules:** 10+
- **API Endpoints:** 7
- **Supported Classes:** 7 (HAM10000)
- **Knowledge Base:** 25+ conditions
- **Training Dataset:** 10,015 images
- **Model Size:** ~13MB

---

<div align="center">

**[⬆ back to top](#dermalens-ai-)**

Made with ❤️ for the open-source dermatology AI community

If you found this project helpful, please consider:
- ⭐ Starring this repository
- 🔗 Sharing with colleagues
- 🐛 Reporting bugs
- 💡 Suggesting improvements

[GitHub](https://github.com/YOUR_USERNAME/dermalens-ai) • [Issues](https://github.com/YOUR_USERNAME/dermalens-ai/issues) • [Discussions](https://github.com/YOUR_USERNAME/dermalens-ai/discussions)

</div>
#   A I - - P O W E R E D - S K I N - L E S I O N - A N A L Y S I S - P L A T F O R M  
 
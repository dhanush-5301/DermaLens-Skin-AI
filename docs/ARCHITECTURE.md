# System Architecture

## Overview

DermaLens AI is a full-stack dermoscopic analysis system that combines:
1. **MobileNetV2 CNN** — Deep learning classifier (HAM10000-trained)
2. **Anthropic Claude** — Large language model for clinical reasoning
3. **FastAPI** — High-performance REST API backend
4. **Single-Page Application** — Pure HTML/CSS/JavaScript frontend

---

## System Components

### 1. Frontend Layer

**Technology:** Vanilla HTML/CSS/JavaScript (no build step required)

```
┌────────────────────────────────────┐
│   Browser (SPA)                    │
├────────────────────────────────────┤
│ • Image Upload (Drag & Drop)       │
│ • Patient Information Form         │
│ • Real-time Progress Indicator     │
│ • Report Visualization             │
│ • Authentication UI                │
└────────┬─────────────────────────────┘
         │ REST API calls
         └──→ http://localhost:8000
```

**Key Features:**
- Single HTML file (`frontend/index.html`)
- No dependencies or build process
- Works offline for inference
- Responsive design for desktop/tablet

**API Interaction:**
```javascript
// Upload image and analyze
const formData = new FormData();
formData.append('file', imageFile);
formData.append('patient_name', 'John Doe');
formData.append('age', '45');

const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData,
    headers: { 'Authorization': `Bearer ${sessionToken}` }
});

const report = await response.json();
```

---

### 2. API Layer (Backend)

**Technology:** FastAPI (Python async framework)

```
┌──────────────────────────────────────────────────┐
│  FastAPI Application (backend/main.py)           │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Authentication Middleware                 │ │
│  │  • Session tokens (JWT-like)               │ │
│  │  • User registration & login               │ │
│  │  • Password hashing (bcrypt)               │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  REST API Endpoints                        │ │
│  │  • POST /api/analyze (multipart/form-data) │ │
│  │  • GET /health                             │ │
│  │  • GET /api/classes                        │ │
│  │  • POST /api/register                      │ │
│  │  • POST /api/login                         │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Image Processing Pipeline                 │ │
│  │  • Format validation (JPEG/PNG/WEBP)       │ │
│  │  • Dimension check & resize                │ │
│  │  • Normalization (HAM10000 stats)          │ │
│  │  • Tensor conversion                       │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**Key Components:**

1. **Routing Layer**
   - FastAPI route handlers for each endpoint
   - Request/response validation using Pydantic
   - CORS middleware for cross-origin requests

2. **Authentication**
   - Session-based auth with in-memory store (prototype)
   - Password hashing using bcrypt
   - JWT-like tokens for stateless auth

3. **Image Processing**
   - PIL/Pillow for image loading and validation
   - NumPy for array operations
   - Format conversion (JPEG → tensor)

---

### 3. Model Layer (Inference)

**Technology:** PyTorch

```
┌────────────────────────────────────────┐
│  CNN Classifier                        │
├────────────────────────────────────────┤
│                                        │
│  Input: 224×224×3 tensor              │
│         ├─ uint8 images               │
│         ├─ normalized by channel      │
│         └─ per-sample normalization   │
│                                        │
│  ↓                                    │
│                                        │
│  MobileNetV2 Backbone                 │
│  ├─ ImageNet pre-trained weights      │
│  ├─ 88 layers                         │
│  └─ 3.5M parameters (efficient)       │
│                                        │
│  ↓                                    │
│                                        │
│  Fine-tuned Head                      │
│  ├─ Last 3 inverted residual blocks   │
│  ├─ Global average pooling            │
│  ├─ Linear classifier (7 classes)     │
│  └─ Softmax activation                │
│                                        │
│  ↓                                    │
│                                        │
│  Temperature Scaling                  │
│  ├─ Learnable temperature T=1.5       │
│  ├─ Better probability calibration    │
│  └─ Confidence scores match accuracy  │
│                                        │
│  Output: Softmax probabilities        │
│  └─ 7-dim vector (0.0-1.0)            │
│                                        │
└────────────────────────────────────────┘
```

**Model Details:**
- **Architecture:** MobileNetV2 (Sandler et al., 2018)
- **Training Dataset:** HAM10000 (10,015 dermoscopy images)
- **Classes:** 7 skin lesion types
- **Input Size:** 224×224×3 RGB
- **Output:** Per-class softmax probabilities
- **Size:** ~13 MB
- **Inference Time:** 150-300ms (CPU), 50-100ms (GPU)

**Training Strategy:**
- Balanced sampling using WeightedRandomSampler
- Focal Loss (γ=2.0) for class imbalance handling
- AdamW optimizer with layer-wise learning rate
- CosineAnnealingWarmRestarts scheduler
- Early stopping on validation accuracy

---

### 4. Language Model Layer (Claude)

**Technology:** Anthropic Claude API

```
┌──────────────────────────────────────────────────┐
│  Claude API (Anthropic Cloud)                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  Input:                                          │
│  • CNN predictions (softmax probs)               │
│  • Patient info (age, location, symptoms)       │
│  • ABCD criteria analysis (rule-based)           │
│  • Differential diagnosis list                   │
│                                                  │
│  ↓ (structured prompt)                         │
│                                                  │
│  Claude-3.5-Sonnet                              │
│  • 200K context window                          │
│  • Medical knowledge from training              │
│  • Advanced reasoning                           │
│                                                  │
│  ↓                                              │
│                                                  │
│  Output:                                         │
│  • Structured clinical report                   │
│  • Differential diagnoses with reasoning        │
│  • Risk stratification                          │
│  • Recommendations & next steps                 │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Fallback Mode:**
- If API key missing or rate-limited → rule-based summaries
- ABCD analysis + knowledge base → formatted report
- System remains functional without Claude

---

### 5. Knowledge Base

**Technology:** Embedded Python dictionaries

```
CONDITION_DATABASE = {
    "melanoma": {
        "icd10": "C43.9",
        "risk": "high",
        "abcd_threshold": 8,
        "dermatologists_needed": True,
        "similar_conditions": ["dysplastic_nevus", "seborrheic_keratosis"],
        "triggers_urgent_referral": True,
    },
    "nevus": {
        "icd10": "D22.9",
        "risk": "low",
        ...
    },
    # ... 25+ more conditions
}
```

**Features:**
- 25+ skin conditions
- ABCD criteria thresholds
- ICD-10 codes for each condition
- Differential diagnosis relationships
- Risk stratification levels
- Clinical flags for urgent referral

---

## Data Flow Diagram

```
┌──────────────┐
│  User uploads│
│  image       │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Frontend SPA             │
│ • Form validation        │
│ • Drag & drop handler    │
│ • Progress indicator     │
└──────┬───────────────────┘
       │
       │ POST /api/analyze
       │ multipart/form-data
       │
       ▼
┌──────────────────────────┐
│ FastAPI Backend          │
│ • Authenticate user      │
│ • Validate image format  │
│ • Store temporary file   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Image Processing         │
│ • Load image (PIL)       │
│ • Resize to 224×224      │
│ • Normalize              │
│ • Convert to tensor      │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ MobileNetV2 CNN          │
│ • Forward pass           │
│ • Get logits             │
│ • Apply temperature      │
│ • Softmax probabilities  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Post-processing          │
│ • Get top-1 prediction   │
│ • Calculate confidence   │
│ • Lookup condition info  │
│ • Build ABCD analysis    │
│ • Generate differential  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Claude API Call          │
│ • Format structured      │
│   prompt                 │
│ • Include predictions    │
│ • Include patient info   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Claude Response          │
│ • Clinical reasoning     │
│ • Formatted report       │
│ • References & citations │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Response Formatting      │
│ • JSON response          │
│ • Include all analysis   │
│ • Clean up temp files    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Frontend SPA             │
│ • Display report         │
│ • Highlight key findings │
│ • Show recommendations   │
└──────────────────────────┘
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML/CSS/JavaScript | Web interface |
| **Backend** | FastAPI | REST API server |
| **Deep Learning** | PyTorch | CNN inference |
| **Model** | MobileNetV2 | Image classification |
| **Language Model** | Claude (Anthropic) | Clinical reasoning |
| **Image Processing** | PIL/NumPy | Preprocessing |
| **Web Server** | Uvicorn | ASGI server |
| **Containerization** | Docker | Deployment |

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Model Size** | ~13 MB |
| **Inference Time (CPU)** | 150-300 ms |
| **Inference Time (GPU)** | 50-100 ms |
| **API Response Time** | 500-2000 ms (includes Claude call) |
| **Memory Usage** | ~500 MB RAM (CPU) |
| **Max File Size** | 15 MB |
| **Supported Formats** | JPEG, PNG, WEBP |

---

## Security Considerations

1. **API Key Management**
   - Store in `.env` file (not in code)
   - Never commit `.env` to version control
   - Use environment variable injection in production

2. **User Input Validation**
   - File format validation (JPEG/PNG/WEBP)
   - File size limit (15 MB)
   - Image dimension checks

3. **Authentication**
   - Session-based (prototype)
   - Password hashing (bcrypt)
   - Stateless token (production)

4. **Data Privacy**
   - Temporary files deleted after processing
   - No persistent storage of images
   - User consent required

---

## Scaling Considerations

### For Production

1. **Database:** Switch from in-memory to PostgreSQL
2. **Queue:** Add Celery/Redis for async processing
3. **Load Balancing:** Use Nginx/HAProxy
4. **Caching:** Redis for frequently accessed data
5. **Monitoring:** Prometheus + Grafana
6. **Logging:** ELK Stack or Cloud Logging

### Model Optimization

1. **Quantization:** Convert to INT8 for faster inference
2. **ONNX Export:** Cross-platform model format
3. **TensorRT:** NVIDIA GPU optimization
4. **Model Serving:** TensorFlow Serving, Triton

---

## Future Architecture Evolution

```
Current (MVP)
├─ Single FastAPI instance
├─ In-memory session store
├─ Local model weights
└─ Synchronous API

↓

Scalable Production
├─ API Gateway (Nginx)
├─ Multiple FastAPI workers (Gunicorn)
├─ PostgreSQL + Redis
├─ Async processing (Celery)
├─ Model serving layer (TensorRT)
├─ Monitoring & logging
└─ Auto-scaling

↓

Enterprise
├─ Kubernetes orchestration
├─ Microservices (API, inference, reporting)
├─ Multi-region deployment
├─ Advanced security (HIPAA compliance)
├─ Model versioning & A/B testing
└─ Real-time monitoring & alerts
```

---

<div align="center">

For more technical details, see [README.md](../README.md)

</div>

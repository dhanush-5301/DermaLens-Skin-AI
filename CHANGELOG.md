# Changelog

All notable changes to DermaLens AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-05-31

### Added

- ✨ **Initial Release**
  - MobileNetV2 CNN trained on HAM10000 dataset
  - Claude AI integration for clinical report generation
  - Single-page application frontend (HTML/CSS/JavaScript)
  - FastAPI backend with REST API
  - Session-based authentication
  - Drag & drop image upload
  - Real-time analysis with progress indication
  - 25+ skin condition knowledge base
  - ABCD criteria analysis
  - ICD-10 code reference
  - Temperature-calibrated confidence scores
  - Docker and Docker Compose support
  - Comprehensive documentation
  - Full API reference
  - Model training script
  - Health check endpoint

### Features

- 🧠 **MobileNetV2 CNN** with 82-86% accuracy on HAM10000
- 🤖 **Claude AI** for clinical reasoning
- 📊 **ABCD Analysis** with automated scoring
- 🎯 **Symptom-Aware** differential diagnosis
- 🖥️ **Zero-Build Frontend** (HTML/CSS/JS only)
- 🔐 **Session Authentication** (prototype)
- 🐳 **Docker-Ready** deployments
- 📈 **Temperature Scaling** for calibrated confidence
- 🚀 **Fast Inference** (150-300ms on CPU)

### Documentation

- README.md with comprehensive overview
- Installation & usage guides
- API reference documentation
- System architecture diagram
- Troubleshooting guide
- Contributing guidelines
- Code of Conduct
- Deployment guide
- License (MIT)

---

## [Unreleased]

### Planned

- [ ] **Multi-Modal Input** — Text + image analysis
- [ ] **Mobile App** — React Native / Flutter
- [ ] **Real-time Webcam** — Live lesion analysis
- [ ] **Patient Dashboard** — History & follow-ups
- [ ] **Vision Transformers** — ViT baseline
- [ ] **Multi-Language** — i18n support
- [ ] **Offline Mode** — Edge deployment
- [ ] **HIPAA Compliance** — Audit logging
- [ ] **Explainability** — LIME/SHAP visualizations
- [ ] **Batch Processing** — Async queue API
- [ ] **Model Monitoring** — Data drift detection
- [ ] **Database Migration** — PostgreSQL + ORM

---

## How to Report Changes

When contributing changes, update this file:

1. Add new section under `[Unreleased]` if not present
2. Use categories: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**, **Security**
3. Keep entries brief and user-focused
4. Link to related issues: `[#123](https://github.com/YOUR_USERNAME/dermalens-ai/issues/123)`

### Example Entry

```markdown
### Fixed

- Fixed image rotation issue for EXIF-encoded JPEGs [#45](...)
- Improved error handling for invalid image formats [#42](...)
```

---

## Version Numbering

- **MAJOR** — Breaking changes (1.0.0 → 2.0.0)
- **MINOR** — New features, backward-compatible (1.0.0 → 1.1.0)
- **PATCH** — Bug fixes, backward-compatible (1.0.0 → 1.0.1)

---

<div align="center">

**See all changes:** [GitHub Releases](https://github.com/YOUR_USERNAME/dermalens-ai/releases)

</div>

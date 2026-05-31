# Contributing to DermaLens AI

Thank you for your interest in contributing to DermaLens AI! This document provides guidelines and instructions for contributing to the project.

## 🎯 Code of Conduct

By participating in this project, you agree to:
- Be respectful and inclusive
- Focus on constructive feedback
- Welcome diverse perspectives
- Report harmful behavior to project maintainers

## 📋 How to Contribute

### 1. **Report Bugs**

If you find a bug, please create an issue with:
- **Title:** Clear, descriptive bug summary
- **Description:** What happened vs. what you expected
- **Steps to Reproduce:** Exact steps to replicate the issue
- **Environment:** Python version, OS, GPU info
- **Error Log:** Full error traceback if applicable

**Example:**
```
Title: Image upload fails with certain JPEG formats

Description:
When uploading a JPEG image with EXIF rotation data, the API returns 
a 500 error instead of processing the image.

Steps to Reproduce:
1. Take a photo on iPhone (has EXIF rotation)
2. Upload to DermaLens
3. See error: "PIL.UnidentifiedImageError"

Environment:
- Python 3.11.2
- Pillow 10.3.0
- macOS 13.6
```

### 2. **Suggest Features**

Feature requests should include:
- **Use Case:** Why this feature is needed
- **Proposed Solution:** Your idea for implementation
- **Alternatives:** Other approaches you've considered
- **Additional Context:** Any relevant information

**Example:**
```
Title: Add real-time webcam input for lesion analysis

Use Case:
Dermatologists could use a webcam instead of uploading images,
making examinations faster during in-office consultations.

Proposed Solution:
- Add WebRTC component to frontend
- Stream frames to /api/analyze-stream endpoint
- Return real-time predictions with 200ms latency

Alternatives:
- Mobile app with camera (more complex)
- Desktop app (limits accessibility)
```

### 3. **Submit Pull Requests**

#### Step 1: Fork & Clone

```bash
# Fork the repository via GitHub UI
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai
```

#### Step 2: Create Feature Branch

```bash
# Use descriptive branch names
git checkout -b feature/add-webcam-support
# or
git checkout -b fix/image-rotation-bug
# or
git checkout -b docs/improve-api-documentation
```

#### Step 3: Make Changes

Follow the coding standards below and commit with clear messages:

```bash
git add .
git commit -m "Add real-time webcam streaming endpoint

- Implement WebRTC stream handler in FastAPI
- Add frontend video element with canvas capture
- Support multiple video codecs (H.264, VP8)
- Add unit tests for stream validation
- Update README with usage example"
```

#### Step 4: Run Tests & Linting

```bash
# Run unit tests
pytest tests/

# Check code style (PEP 8)
pylint backend/ --disable=R,C

# Format code
black backend/
```

#### Step 5: Push & Create PR

```bash
git push origin feature/add-webcam-support
# Then create PR via GitHub UI
```

In your PR description, include:
- **What:** Brief summary of changes
- **Why:** Motivation and context
- **How:** Implementation approach
- **Testing:** How you tested the changes
- **Closes:** Reference related issues (e.g., "Closes #42")

**Example PR Description:**
```
## What
Add real-time webcam streaming for dermoscopy analysis

## Why
Dermatologists need faster image capture during consultations.
Currently requires manual photo upload, which takes 30+ seconds.

## How
- New `/api/analyze-stream` endpoint accepts frame batch
- Frontend captures canvas frames every 33ms (30 FPS)
- Server returns predictions in real-time

## Testing
- ✅ Tested with webcam from 3 devices (macOS, Windows, Android)
- ✅ Verified 200ms latency on CPU-only backend
- ✅ Added unit tests (see tests/test_stream.py)
- ✅ Works with Firefox, Chrome, Safari

## Closes
#123
```

---

## 📐 Coding Standards

### Python Style Guide (PEP 8)

```python
# ✅ Good: Clear, documented, follows conventions

def analyze_image(image_path: str, model_weights: Path) -> Dict[str, float]:
    """
    Analyze a dermoscopic image using the trained classifier.
    
    Args:
        image_path: Path to input image file (JPEG/PNG)
        model_weights: Path to PyTorch model weights
        
    Returns:
        Dictionary with class predictions and confidence scores.
        Keys: class names (e.g., 'melanoma', 'nevus')
        Values: confidence scores (0.0 to 1.0)
        
    Raises:
        FileNotFoundError: If image or model weights not found
        ValueError: If image dimensions invalid
    """
    # Implementation
    pass


# ❌ Bad: Unclear, no documentation

def analyze(img, wts):
    # do analysis
    return predictions
```

### Key Standards

- **Naming:** Use `snake_case` for variables/functions, `PascalCase` for classes
- **Line Length:** Max 100 characters (use `black` formatter)
- **Type Hints:** Add for function signatures
- **Docstrings:** Use Google-style docstrings
- **Comments:** Explain "why", not "what" (code explains itself)
- **Imports:** Organize alphabetically, separate stdlib/third-party/local

```python
# ✅ Good import organization
import json
import logging
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch
from fastapi import FastAPI
from PIL import Image

from backend.models import MobileNetV2Classifier
```

### Frontend (HTML/CSS/JavaScript)

- **HTML:** Semantic elements, proper structure
- **CSS:** BEM naming convention (`block__element--modifier`)
- **JavaScript:** ES6+, clear variable names, avoid global state

```javascript
// ✅ Good: Clear, modular, documented

class ImageAnalyzer {
    /**
     * Upload and analyze a dermoscopic image.
     * @param {File} imageFile - The image file to analyze
     * @returns {Promise<Object>} Clinical report
     */
    async analyzeImage(imageFile) {
        const formData = new FormData();
        formData.append('file', imageFile);
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData,
        });
        
        return response.json();
    }
}
```

---

## 🧪 Testing

### Writing Tests

Create tests in `tests/` directory:

```python
# tests/test_image_processing.py
import pytest
from pathlib import Path
from backend.image_processing import preprocess_image

def test_preprocess_image_valid():
    """Test preprocessing with valid 224x224 image."""
    test_image = Path("tests/fixtures/test_image.jpg")
    result = preprocess_image(test_image)
    
    assert result.shape == (1, 3, 224, 224)
    assert result.dtype == torch.float32

def test_preprocess_image_invalid_format():
    """Test preprocessing rejects invalid formats."""
    with pytest.raises(ValueError):
        preprocess_image("image.bmp")  # Unsupported format
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_image_processing.py

# Run with coverage
pytest --cov=backend tests/
```

---

## 📚 Documentation

### Updating README.md

When adding features, update the relevant sections:

1. **Features section** — Add bullet point describing new feature
2. **API Reference** — Add endpoint documentation
3. **Installation** — Update if new dependencies added
4. **Usage** — Add example usage
5. **Future Improvements** — Remove if implemented

### Creating New Docs

Place documentation files in `docs/`:

- **docs/API.md** — Detailed API documentation
- **docs/ARCHITECTURE.md** — System design and components
- **docs/DEPLOYMENT.md** — Production deployment guide
- **docs/TROUBLESHOOTING.md** — Common issues and solutions
- **docs/TRAINING.md** — Model training guide

---

## 🔄 Review Process

### What Happens After You Submit a PR

1. **Automated Checks** (GitHub Actions)
   - ✅ Unit tests must pass
   - ✅ Code style checks (black, pylint)
   - ✅ Coverage should not decrease

2. **Manual Review**
   - Code quality and architecture
   - Documentation completeness
   - Testing coverage
   - Performance impact

3. **Feedback & Iteration**
   - Maintainers may request changes
   - Update your PR based on feedback
   - Conversation continues until approval

4. **Merge**
   - Once approved, PR is merged to `main`
   - Your contribution is now live!

---

## 📝 Commit Message Guidelines

Write clear, semantic commit messages following Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation changes
- **style:** Code style (formatting, missing semicolons, etc.)
- **refactor:** Code refactoring without feature changes
- **perf:** Performance improvements
- **test:** Adding/updating tests
- **chore:** Build, dependencies, tooling

### Examples

```
✅ GOOD:
feat(api): Add real-time image analysis streaming endpoint
fix(preprocessing): Handle EXIF rotation for uploaded images
docs(readme): Update installation instructions for Windows
refactor(model): Simplify temperature calibration logic
test(backend): Add unit tests for Claude API integration

❌ BAD:
update
fix bug
final
update readme
WIP
```

---

## 🚀 Getting Help

### Questions?

- 📖 **Read the Docs:** [docs/](docs/) folder
- 💬 **GitHub Discussions:** [Discussions tab](https://github.com/YOUR_USERNAME/dermalens-ai/discussions)
- 📧 **Email:** your-email@example.com
- 🐛 **Issues:** Search existing issues for similar questions

### Development Setup Help

```bash
# Problems with dependencies?
pip install -r requirements.txt --upgrade

# Virtual environment not working?
python -m venv venv --clear
venv\Scripts\activate

# CUDA issues?
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

---

## 🎁 Recognition

Contributors will be:
- ⭐ Listed in [README.md](README.md#-author--contributors)
- 🏆 Recognized in release notes
- 🎖️ Added to GitHub Contributors

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Thank you for making DermaLens AI better! Your contributions help advance open-source dermatology AI.

---

<div align="center">

**Questions? Feel free to reach out!**

[Open an Issue](https://github.com/YOUR_USERNAME/dermalens-ai/issues/new) • [Start a Discussion](https://github.com/YOUR_USERNAME/dermalens-ai/discussions/new) • [Contact Us](mailto:your-email@example.com)

</div>

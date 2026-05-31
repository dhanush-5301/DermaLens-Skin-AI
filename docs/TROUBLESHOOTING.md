# Troubleshooting Guide

Common issues and solutions for DermaLens AI.

---

## Installation & Setup Issues

### ModuleNotFoundError: No module named 'torch'

**Error:**
```
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'torch'
```

**Solutions:**

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Reinstall PyTorch:**
   ```bash
   # For CPU
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   
   # For GPU (CUDA 11.8)
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Verify installation:**
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

---

### ModuleNotFoundError: No module named 'fastapi'

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
pip install fastapi uvicorn python-multipart
```

---

### Virtual Environment Issues

**Error:**
```
Command 'python' not found
# or
pip: command not found
```

**Solutions:**

1. **Verify Python installation:**
   ```bash
   python --version
   # or
   python3 --version
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Activate virtual environment:**
   ```bash
   # Linux / macOS
   source venv/bin/activate
   
   # Windows (Command Prompt)
   venv\Scripts\activate
   
   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   ```

---

## API & Server Issues

### ANTHROPIC_API_KEY not found

**Error:**
```
KeyError: 'ANTHROPIC_API_KEY'
# or
ANTHROPIC_API_KEY is not set
```

**Solutions:**

1. **Verify .env file exists:**
   ```bash
   ls -la .env
   # or on Windows: dir .env
   ```

2. **Check file content:**
   ```bash
   cat .env
   # Look for: ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Create .env from example:**
   ```bash
   cp .env.example .env
   nano .env  # Edit and add your API key
   ```

4. **Verify API key format:**
   - Must start with `sk-ant-`
   - Get from: https://console.anthropic.com/keys
   - Check for typos or extra spaces

---

### Port 8000 already in use

**Error:**
```
Address already in use: ('127.0.0.1', 8000)
# or
OSError: [WinError 10048] Only one usage of each socket address
```

**Solutions:**

1. **Use a different port:**
   ```bash
   uvicorn backend.main:app --port 8001
   ```

2. **Kill process using port 8000:**
   
   **Linux/macOS:**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```
   
   **Windows:**
   ```powershell
   Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
   ```

3. **Change port in .env:**
   ```
   PORT=8001
   ```

---

### Connection refused at localhost:8000

**Error:**
```
ConnectionRefusedError: [Errno 111] Connection refused
# or
Failed to connect to localhost:8000
```

**Solutions:**

1. **Start the server:**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

2. **Check if server is running:**
   ```bash
   ps aux | grep uvicorn
   # or
   netstat -tuln | grep 8000
   ```

3. **Verify firewall:**
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 8000/tcp
   
   # Windows: Check Windows Defender Firewall
   ```

4. **Check logs:**
   ```bash
   tail -f logs/dermalens.log
   ```

---

### 500 Internal Server Error

**Error:**
```
HTTP 500 - Internal Server Error
```

**Solutions:**

1. **Check server logs:**
   ```bash
   tail -f logs/dermalens.log
   # Look for the actual error message
   ```

2. **Check API key:**
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ANTHROPIC_API_KEY'))"
   ```

3. **Verify model file exists:**
   ```bash
   ls -la models/dermalens_mobilenetv2.pth
   ```

4. **Test with curl:**
   ```bash
   curl -X GET http://localhost:8000/health
   ```

---

## Image Upload Issues

### "Invalid image format"

**Error:**
```
ValueError: Invalid image format
# or
PIL.UnidentifiedImageError: cannot identify image file
```

**Solutions:**

1. **Supported formats:** JPEG, PNG, WEBP
   ```bash
   file myimage.jpg
   # Should show: myimage.jpg: JPEG image data, ...
   ```

2. **Convert image format:**
   ```bash
   # Using ImageMagick
   convert myimage.bmp myimage.jpg
   
   # Or use online converter
   ```

3. **Check file permissions:**
   ```bash
   chmod 644 myimage.jpg
   ```

4. **File is corrupted:**
   - Try re-downloading the image
   - Open in image viewer to verify

---

### "File too large"

**Error:**
```
File size exceeds maximum allowed: 15MB
```

**Solutions:**

1. **Reduce image quality:**
   ```bash
   # Using ImageMagick
   convert input.jpg -quality 85 -resize 80% output.jpg
   ```

2. **Change max file size:**
   - Edit `backend/main.py`
   - Find: `MAX_FILE_SIZE = 15 * 1024 * 1024`
   - Increase value (not recommended)

3. **Use smaller image:**
   - Original image should be < 15MB
   - Typical dermoscopy images are < 5MB

---

### "Timeout: Image processing took too long"

**Error:**
```
TimeoutError: Request timed out after 60 seconds
```

**Solutions:**

1. **Check system resources:**
   ```bash
   free -h  # Memory
   df -h    # Disk space
   top      # CPU usage
   ```

2. **Increase timeout:**
   - In frontend: Increase `fetch()` timeout
   - In server: Increase FastAPI timeout

3. **GPU acceleration:**
   ```bash
   # Check GPU availability
   python -c "import torch; print(torch.cuda.is_available())"
   
   # If available, use CUDA in model
   ```

---

## Claude API Issues

### Rate limit exceeded

**Error:**
```
RateLimitError: Rate limit exceeded
# or
429 Too Many Requests
```

**Solutions:**

1. **Add retry logic:**
   ```python
   import time
   max_retries = 3
   for attempt in range(max_retries):
       try:
           response = client.messages.create(...)
           break
       except RateLimitError:
           if attempt < max_retries - 1:
               time.sleep(2 ** attempt)  # Exponential backoff
   ```

2. **Reduce request frequency:**
   - Implement request queuing
   - Add delays between API calls

3. **Check API quota:**
   - Visit: https://console.anthropic.com/account/limits
   - Upgrade plan if needed

---

### "API key not valid"

**Error:**
```
AuthenticationError: Invalid API key
# or
401 Unauthorized
```

**Solutions:**

1. **Verify API key:**
   - Copy from: https://console.anthropic.com/keys
   - Ensure no extra spaces or line breaks

2. **Check key format:**
   - Must start with `sk-ant-`
   - Must be 60+ characters

3. **Regenerate key if needed:**
   - Go to: https://console.anthropic.com/account/keys
   - Delete old key, create new one

4. **Check environment loading:**
   ```python
   from dotenv import load_dotenv
   import os
   load_dotenv()
   key = os.getenv('ANTHROPIC_API_KEY')
   print(f"Loaded key: {key[:10]}...")  # Print first 10 chars
   ```

---

### Claude not generating reports

**Error:**
```
No clinical report generated
# or
Claude response was empty
```

**Solutions:**

1. **Check fallback mode:**
   - System should use rule-based reports if Claude unavailable
   - If not, there's likely an API issue

2. **Test API directly:**
   ```python
   from anthropic import Anthropic
   client = Anthropic(api_key="sk-ant-...")
   msg = client.messages.create(
       model="claude-3-5-sonnet-20241022",
       max_tokens=1024,
       messages=[{"role": "user", "content": "Hello"}]
   )
   print(msg.content[0].text)
   ```

3. **Check prompt formatting:**
   - Verify prompt syntax in `backend/main.py`
   - Ensure placeholders are filled correctly

---

## Model & Inference Issues

### Model weights file not found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/dermalens_mobilenetv2.pth'
```

**Solutions:**

1. **Download pre-trained model:**
   ```bash
   cd models/
   wget https://your-download-link/dermalens_mobilenetv2.pth
   ```

2. **Train model yourself:**
   ```bash
   python train.py --data_dir data/HAM10000 --epochs 30
   ```

3. **Check model path:**
   ```bash
   ls -la models/
   # Should show: dermalens_mobilenetv2.pth
   ```

---

### "CUDA out of memory"

**Error:**
```
RuntimeError: CUDA out of memory. Tried to allocate ...
```

**Solutions:**

1. **Use CPU instead:**
   ```python
   device = torch.device('cpu')
   # or set: CUDA_VISIBLE_DEVICES=""
   ```

2. **Reduce batch size:**
   ```bash
   python train.py --batch_size 16  # Instead of 64
   ```

3. **Clear GPU cache:**
   ```python
   torch.cuda.empty_cache()
   ```

4. **Reduce image size:**
   - System uses 224×224 input
   - Not easily changeable without retraining

---

### Poor prediction accuracy

**Error:**
```
Model predictions don't seem accurate
```

**Solutions:**

1. **Verify model weights:**
   ```bash
   file models/dermalens_mobilenetv2.pth
   # Should be > 50MB
   ```

2. **Check input preprocessing:**
   - Verify normalization is correct
   - Check image resizing

3. **Test with sample images:**
   ```bash
   python diagnose.py --image sample.jpg
   ```

4. **Retrain model:**
   - Ensure HAM10000 dataset downloaded correctly
   - Check for class imbalance

---

## Docker Issues

### Docker image build fails

**Error:**
```
Error building docker image: ...
```

**Solutions:**

1. **Check Docker installation:**
   ```bash
   docker --version
   docker ps
   ```

2. **Clean up and rebuild:**
   ```bash
   docker system prune -a
   docker build -t dermalens-ai:latest .
   ```

3. **Check Dockerfile:**
   - Verify all commands are valid
   - Ensure requirements.txt exists

---

### Container won't start

**Error:**
```
Error response from daemon: ...
```

**Solutions:**

1. **Check logs:**
   ```bash
   docker logs dermalens
   ```

2. **Verify environment variables:**
   ```bash
   docker exec dermalens env
   ```

3. **Run with verbose output:**
   ```bash
   docker run -it dermalens-ai:latest bash
   ```

---

## Performance Issues

### Slow inference (> 1 second)

**Solutions:**

1. **Use GPU:**
   ```bash
   docker run --gpus all dermalens-ai:latest
   ```

2. **Check system resources:**
   ```bash
   top  # CPU usage
   free -h  # Memory
   ```

3. **Reduce concurrent requests:**
   - Implement request queuing
   - Add rate limiting

4. **Model optimization:**
   - Quantize to INT8
   - Export to ONNX for faster inference

---

### High memory usage

**Solutions:**

1. **Monitor memory:**
   ```bash
   ps aux | grep python
   ```

2. **Reduce worker count:**
   - Edit gunicorn config: `--workers 2`

3. **Enable memory profiling:**
   ```python
   from memory_profiler import profile
   
   @profile
   def analyze_image():
       ...
   ```

---

## General Debugging

### Enable debug logging

```bash
# Set log level to debug
export LOG_LEVEL=debug
uvicorn backend.main:app --log-level debug

# Or in .env:
LOG_LEVEL=debug
```

### Check system info

```bash
# Python version
python --version

# Available memory
free -h

# Disk space
df -h

# CPU info
nproc  # Number of CPUs
lscpu  # CPU details

# CUDA (if GPU)
nvidia-smi
```

### Test connectivity

```bash
# Test internet connection
ping google.com

# Test API endpoint
curl -X GET http://localhost:8000/health

# Test Claude API
python -c "
from anthropic import Anthropic
client = Anthropic(api_key='sk-ant-...')
print('Connection OK')
"
```

---

## Getting Help

### Resources

- 📖 **Documentation:** [README.md](../README.md)
- 🏗️ **Architecture:** [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- 🚀 **Deployment:** [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/dermalens-ai/discussions)
- 🐛 **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/dermalens-ai/issues)

### Creating a Bug Report

When reporting issues, include:

1. **Error message** (full traceback)
2. **System info** (OS, Python version)
3. **Steps to reproduce**
4. **Expected vs actual behavior**
5. **Logs** (from `logs/dermalens.log`)

**Example:**
```
**Error:**
ModuleNotFoundError: No module named 'torch'

**System:**
- OS: Ubuntu 20.04
- Python: 3.11.2
- pip: 23.0.1

**Steps:**
1. Clone repo
2. Create venv
3. Run: pip install -r requirements.txt
4. Run: uvicorn backend.main:app

**Expected:** Server starts on port 8000
**Actual:** Error on import

**Logs:**
[Full traceback here]
```

---

<div align="center">

**Still stuck?** 📞 [Contact us](mailto:your-email@example.com) or [open an issue](https://github.com/YOUR_USERNAME/dermalens-ai/issues/new)

</div>

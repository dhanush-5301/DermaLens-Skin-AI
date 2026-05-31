# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in DermaLens AI, please **do not** open a public GitHub issue. Instead, please report it responsibly to:

**Email:** your-email@example.com

**Please include:**
1. Description of the vulnerability
2. Steps to reproduce
3. Impact assessment
4. Suggested fix (if available)

We will acknowledge your report within 24 hours and work with you to fix the issue promptly.

---

## Security Best Practices

### For Users

1. **Keep software updated**
   - Regularly update DermaLens AI
   - Update Python and dependencies: `pip install -r requirements.txt --upgrade`

2. **API Key Management**
   - Never share your ANTHROPIC_API_KEY
   - Store in `.env` file (never in code)
   - Rotate keys periodically
   - Revoke old keys at console.anthropic.com

3. **Firewall & Network**
   - Only expose necessary ports (80, 443)
   - Use HTTPS in production (not HTTP)
   - Restrict API access by IP if possible

4. **Data Privacy**
   - Don't upload real patient data to public demos
   - Use HIPAA-compliant deployments for medical data
   - Enable audit logging for compliance

### For Developers

1. **Code Review**
   - All changes reviewed before merge
   - Security-focused code review process
   - Dependency vulnerability scanning

2. **Dependency Management**
   - Pin dependency versions in `requirements.txt`
   - Regular updates: `pip install --upgrade -r requirements.txt`
   - Check for vulnerabilities: `pip check`

3. **Environment Variables**
   ```bash
   # ✅ Good
   ANTHROPIC_API_KEY=sk-ant-...  # In .env
   
   # ❌ Bad
   key = "sk-ant-..."  # In source code
   ```

4. **Input Validation**
   - All user inputs validated
   - File format/size checks enforced
   - SQL injection protection (if using database)

5. **HTTPS & TLS**
   - Always use HTTPS in production
   - Use valid SSL certificates
   - Redirect HTTP to HTTPS

---

## Vulnerability Disclosure Timeline

1. **Day 0:** Report received
2. **Day 1:** Acknowledgment sent
3. **Day 7:** Initial assessment completed
4. **Day 14:** Fix developed & tested
5. **Day 21:** Patch released
6. **Day 30:** Security advisory published

---

## Supported Versions

| Version | Supported          | Security Updates |
|---------|-------------------|------------------|
| 1.x     | ✅ Yes            | Yes              |
| < 1.0   | ❌ No             | No               |

---

## Security Checklist for Deployment

- [ ] Change default credentials
- [ ] Enable HTTPS with valid certificate
- [ ] Configure firewall (allow 80, 443 only)
- [ ] Set strong API key
- [ ] Enable logging and monitoring
- [ ] Regular backups enabled
- [ ] Database encryption enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers configured

---

## Known Security Considerations

### Authentication (Prototype)

Current authentication is **prototype-level**:
- In-memory session store (not persistent)
- No production-grade encryption
- Not suitable for sensitive medical data

**Recommended:** Use enterprise identity providers (OAuth2, SAML) in production.

### Image Storage

Currently:
- Temporary files deleted after processing
- No persistent image storage
- Suitable for demo/research

**Production:** Use encrypted object storage (S3, GCS) with access controls.

### API Rate Limiting

Implement rate limiting to prevent abuse:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request):
    ...
```

---

## Dependencies & Vulnerabilities

### How to Check

```bash
# Check for known vulnerabilities
pip check

# Detailed vulnerability scan
pip-audit

# Check outdated packages
pip list --outdated
```

### Regular Updates

```bash
# Update all packages
pip install -r requirements.txt --upgrade

# Check compatibility
pytest  # Run full test suite
```

### Pin Versions

```bash
# requirements.txt should pin major versions
fastapi==0.111.0
torch>=2.2.0,<3.0.0
```

---

## Compliance & Standards

### Medical Device Regulations

⚠️ **Important:** DermaLens is **NOT FDA-approved** and is **NOT a medical device**.

- Not intended for clinical diagnosis
- For research and educational purposes only
- Cannot replace professional medical advice

### HIPAA Compliance (if needed)

For handling real patient data:
- [ ] Implement Business Associate Agreements (BAA)
- [ ] Enable encryption at rest and in transit
- [ ] Implement audit logging
- [ ] Use secure password policies
- [ ] Regular security assessments

---

## Security Contacts

- **Responsible Disclosure:** your-email@example.com
- **General Security Questions:** your-email@example.com
- **GitHub Security Advisory:** [Report via GitHub](https://github.com/YOUR_USERNAME/dermalens-ai/security/advisories)

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Guide](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

<div align="center">

**Thank you for helping keep DermaLens AI secure!**

</div>

# Security Patch Log

## 2026-02-10: Critical Vulnerability Updates

### Updated Packages

| Package | CVE | Severity | From | To | Status |
|---------|-----|----------|------|-----|--------|
| langsmith | CVE-2026-25528 | Medium | 0.5.2 | 0.6.3 | ✅ Patched |
| pypdf | CVE-2026-24688, CVE-2026-22691, CVE-2026-22690 | Medium/Low | 6.5.0 | 6.6.2 | ✅ Patched |
| python-multipart | CVE-2026-24486 | High | 0.0.21 | 0.0.22 | ✅ Patched |
| protobuf | CVE-2026-0994 | High | < 5.29.6 | 5.29.6 | ✅ Patched |
| urllib3 | CVE-2026-21441 | High | < 2.6.3 | 2.6.3 | ✅ Already Patched |

### Vulnerability Descriptions

1. **CVE-2026-25528 (langsmith)**: Server-Side Request Forgery via Tracing Header Injection
   - Fixed by upgrading to langsmith>=0.6.3

2. **CVE-2026-24688 (pypdf)**: Infinite Loop when processing outlines/bookmarks
   - Fixed by upgrading to pypdf>=6.6.2

3. **CVE-2026-24486 (python-multipart)**: Arbitrary File Write via Path Traversal
   - Fixed by upgrading to python-multipart>=0.0.22

4. **CVE-2026-0994 (protobuf)**: JSON recursion depth bypass
   - Fixed by upgrading to protobuf>=5.29.6

5. **CVE-2026-21441 (urllib3)**: Decompression bomb vulnerability
   - Fixed by upgrading to urllib3>=2.6.3

### Verification

Run the following command to verify patches:
```bash
pip-audit --desc --format=table
```

All High and Medium severity vulnerabilities have been addressed.

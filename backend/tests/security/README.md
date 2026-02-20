# Security Audit Tests

Comprehensive security tests for the TutorFlow API.

## Running Security Tests

### Run all security tests:
```bash
cd backend
pytest tests/security/ -v
```

### Run specific test file:
```bash
pytest tests/security/test_jwt_security.py -v
pytest tests/security/test_sql_injection.py -v
pytest tests/security/test_xss_prevention.py -v
pytest tests/security/test_auth_security.py -v
pytest tests/security/test_input_validation.py -v
```

### Run with coverage:
```bash
pytest tests/security/ --cov=../ --cov-report=html
```

## Test Categories

### 1. JWT Security (`test_jwt_security.py`)
- Token expiration validation
- Invalid token rejection
- Token tampering detection
- Refresh token rotation
- Strong algorithm usage

**Requirements**: TokenService from infrastructure

### 2. SQL Injection Prevention (`test_sql_injection.py`)
- SQL injection in URL parameters
- SQL injection in request body
- SQL injection in query strings
- Parameterized query verification

**Requirements**: E2E test fixtures with database

### 3. XSS Prevention (`test_xss_prevention.py`)
- XSS in booking notes
- XSS in review content
- XSS in tutor replies
- XSS in attendance notes
- Content-Type header verification
- JSON response escaping

**Requirements**: E2E test fixtures

### 4. Authentication Security (`test_auth_security.py`)
- Protected endpoint authentication
- Invalid token rejection
- Malformed auth header handling
- Role-based access control
- User data isolation
- Password hashing verification

**Requirements**: Auth endpoints (partially implemented)

### 5. Input Validation (`test_input_validation.py`)
- Past date rejection
- Invalid time format rejection
- Rating bounds validation
- Required field validation
- Long input handling
- Special character handling
- JSON validation

**Requirements**: E2E test fixtures

## Security Test Fixtures

### `security_client`
Client configured with security testing headers

### `xss_payloads`
Common XSS payloads for testing

### `sql_injection_payloads`
Common SQL injection payloads

### `path_traversal_payloads`
Path traversal attack payloads

### `ddos_payloads`
Payloads that might trigger DoS

## OWASP Top 10 Coverage

The security tests cover these OWASP Top 10 categories:

1. **A01:2021 – Broken Access Control**
   - `test_auth_security.py`: Role-based access control tests

2. **A02:2021 – Cryptographic Failures**
   - `test_jwt_security.py`: JWT token security
   - `test_auth_security.py`: Password hashing verification

3. **A03:2021 – Injection**
   - `test_sql_injection.py`: SQL injection prevention

4. **A04:2021 – Insecure Design**
   - Input validation tests across all files

5. **A05:2021 – Security Misconfiguration**
   - Content-Type header verification
   - Security headers verification

6. **A06:2021 – Vulnerable and Outdated Components**
   - (Covered by dependency scanning tools)

7. **A07:2021 – Identification and Authentication Failures**
   - JWT security tests
   - Auth flow tests

8. **A08:2021 – Software and Data Integrity Failures**
   - Token tampering detection

9. **A09:2021 – Security Logging and Monitoring Failures**
   - (Covered by monitoring infrastructure)

10. **A10:2021 – Server-Side Request Forgery (SSRF)**
    - (To be added when external service calls are implemented)

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run security tests
        run: |
          pytest tests/security/ -v --cov=../ --cov-report=xml
```

## Additional Security Tools

Consider integrating:

1. **Dependency Scanning**
   - `safety check` - Check for known vulnerabilities
   - `pip-audit` - Audit dependencies for vulnerabilities

2. **Static Analysis**
   - `bandit` - Security linter for Python
   - `semgrep` - Static code analysis

3. **Secret Scanning**
   - `git-secrets` - Prevent committing secrets
   - `truffleHog` - Find secrets in code

4. **Dynamic Analysis**
   - `OWASP ZAP` - Web application security scanner
   - `sqlmap` - SQL injection scanner

## Notes

- Some tests use placeholders since auth is not fully implemented
- Tests will be updated as authentication is completed
- All tests use the E2E test database, never production
- Security tests are safe to run frequently (no destructive payloads)

## Future Additions

- [ ] CSRF token validation
- [ ] Rate limiting tests
- [ ] File upload security tests
- [ ] API abuse prevention tests
- [ ] Session fixation tests
- [ ] CORS security tests

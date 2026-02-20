"""Fixtures for security tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def security_client(e2e_client: AsyncClient) -> AsyncClient:
    """Client configured for security testing.

    Includes:
    - Malicious headers
    - Unusual user agents
    - Large payloads
    """
    # Configure client for security testing
    e2e_client.headers.update({
        "User-Agent": "Security-Scanner/1.0",
        "X-Forwarded-For": "127.0.0.1",
    })
    return e2e_client


@pytest.fixture
def xss_payloads():
    """Common XSS payloads for testing."""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "';alert('XSS');//",
        "\";alert('XSS');//",
        "<marquee onstart=alert('XSS')>",
        "<isindex action=javascript:alert('XSS') type=submit>",
        "<details open ontoggle=alert('XSS')>",
    ]


@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection payloads for testing."""
    return [
        "1' OR '1'='1",
        "1' UNION SELECT NULL--",
        "1' AND 1=1--",
        "1; DROP TABLE users--",
        "1' OR '1'='1'--",
        "admin'--",
        "admin' OR '1'='1",
        "'; SELECT SLEEP(10)--",
        "1' EXEC xp_cmdshell('dir')--",
        "-1' OR '1'='1",
    ]


@pytest.fixture
def path_traversal_payloads():
    """Path traversal payloads for testing."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "....//....//....//etc/passwd",
        "%2e%2e%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc%252fpasswd",
        "....\\\\....\\\\....\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
    ]


@pytest.fixture
def ddos_payloads():
    """Payloads that might trigger DoS."""
    return [
        "A" * 10000,  # Large string
        "<script>" * 1000,  # Repeated tags
        "1" * 100000,  # Very large number
    ]

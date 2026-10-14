"""
ChainSentinel - Pytest Configuration and Test Isolation Fixtures
Guarantees deterministic, offline-safe test execution by disabling unmocked external network calls.
"""

import urllib.error
import urllib.request
import pytest


@pytest.fixture(autouse=True)
def isolate_network_during_tests(monkeypatch):
    """
    Prevents tests from hitting live blockchain JSON-RPC endpoints over the internet.
    Tests that require specific RPC responses mock LiveBlockchainProvider._rpc_call directly.
    """
    original_urlopen = urllib.request.urlopen

    def safe_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        # Block external blockchain RPC domains during tests
        blocked_keywords = ("http://", "https://")
        if any(url.startswith(prefix) for prefix in blocked_keywords):
            raise urllib.error.URLError("Live network access disabled in automated test suite")
        return original_urlopen(req, *args, **kwargs)

    monkeypatch.setattr(urllib.request, "urlopen", safe_urlopen)

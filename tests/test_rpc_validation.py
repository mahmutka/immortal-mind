"""
tests/test_rpc_validation.py

Unit tests for _validate_rpc_url — SSRF and DNS-rebinding protection.
"""

from unittest.mock import patch
import pytest

from storage.blockchain_anchor import _validate_rpc_url


class TestLiteralIPBlocking:
    """Literal IP addresses in the URL must be blocked if private/reserved."""

    def test_loopback_ipv4_rejected(self):
        assert _validate_rpc_url("http://127.0.0.1:8545") is False

    def test_loopback_ipv4_alt_rejected(self):
        assert _validate_rpc_url("http://127.0.0.2/rpc") is False

    def test_private_class_a_rejected(self):
        assert _validate_rpc_url("http://10.0.0.1/rpc") is False

    def test_private_class_b_rejected(self):
        assert _validate_rpc_url("http://172.16.0.1/rpc") is False

    def test_private_class_c_rejected(self):
        assert _validate_rpc_url("http://192.168.1.1/rpc") is False

    def test_link_local_metadata_rejected(self):
        assert _validate_rpc_url("http://169.254.169.254/latest/meta-data") is False

    def test_link_local_ecs_rejected(self):
        assert _validate_rpc_url("http://169.254.170.2/v2/metadata") is False

    def test_ipv6_loopback_rejected(self):
        assert _validate_rpc_url("http://[::1]:8545") is False


class TestBlockedHostnames:
    """Known metadata hostnames must be blocked before DNS resolution."""

    def test_aws_metadata_hostname_rejected(self):
        assert _validate_rpc_url("http://169.254.169.254/rpc") is False

    def test_gcp_metadata_hostname_rejected(self):
        assert _validate_rpc_url("http://metadata.google.internal/rpc") is False

    def test_alibaba_metadata_rejected(self):
        assert _validate_rpc_url("http://100.100.100.200/rpc") is False


class TestSchemeValidation:
    """Only http and https schemes are allowed."""

    def test_file_scheme_rejected(self):
        assert _validate_rpc_url("file:///etc/passwd") is False

    def test_ftp_scheme_rejected(self):
        assert _validate_rpc_url("ftp://example.com/rpc") is False

    def test_empty_url_rejected(self):
        assert _validate_rpc_url("") is False

    def test_no_host_rejected(self):
        assert _validate_rpc_url("https://") is False


class TestDNSRebindingProtection:
    """Hostnames that resolve to private IPs must be rejected (rebinding guard)."""

    def test_hostname_resolving_to_loopback_rejected(self):
        # Simulate evil.com resolving to 127.0.0.1 after rebinding
        mock_result = [(None, None, None, None, ("127.0.0.1", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://evil.com/rpc") is False

    def test_hostname_resolving_to_private_rejected(self):
        mock_result = [(None, None, None, None, ("192.168.1.1", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://evil.com/rpc") is False

    def test_hostname_resolving_to_link_local_rejected(self):
        mock_result = [(None, None, None, None, ("169.254.169.254", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://evil.com/rpc") is False

    def test_unresolvable_hostname_rejected(self):
        import socket as _socket
        with patch("socket.getaddrinfo", side_effect=_socket.gaierror("NXDOMAIN")):
            assert _validate_rpc_url("https://nonexistent.invalid/rpc") is False

    def test_hostname_resolving_to_public_ip_allowed(self):
        # A legitimate public RPC endpoint
        mock_result = [(None, None, None, None, ("1.2.3.4", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://rpc.example.com/") is True

    def test_all_records_checked_first_public_second_private(self):
        # If any resolved IP is private, the whole URL is rejected
        mock_result = [
            (None, None, None, None, ("1.2.3.4", 0)),
            (None, None, None, None, ("127.0.0.1", 0)),
        ]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://dual-stack.example.com/rpc") is False


class TestLegitimateURLs:
    """Known-good public RPC endpoints must pass validation."""

    def test_base_sepolia_rpc(self):
        mock_result = [(None, None, None, None, ("1.2.3.4", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://sepolia.base.org") is True

    def test_arbitrum_sepolia_rpc(self):
        mock_result = [(None, None, None, None, ("5.6.7.8", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://sepolia-rollup.arbitrum.io/rpc") is True

    def test_https_with_port(self):
        # 8.8.8.8 is a genuine public IP (Google DNS) — not reserved/private
        mock_result = [(None, None, None, None, ("8.8.8.8", 0))]
        with patch("socket.getaddrinfo", return_value=mock_result):
            assert _validate_rpc_url("https://rpc.example.com:8545") is True

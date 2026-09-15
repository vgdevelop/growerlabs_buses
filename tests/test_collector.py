import ssl

from app.services.cache import MemorySnapshotCache
from app.services.collector import INTERMEDIATE_CA, RealtimeCollector


def test_collector_keeps_tls_verification_with_official_intermediate_chain():
    collector = RealtimeCollector("https://example.invalid", 10, MemorySnapshotCache(45))

    assert INTERMEDIATE_CA.is_file()
    assert collector._ssl_context.check_hostname is True
    assert collector._ssl_context.verify_mode == ssl.CERT_REQUIRED

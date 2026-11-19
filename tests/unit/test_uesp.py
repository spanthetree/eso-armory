import urllib.error

from app import uesp


def test_uesp_first_then_the_proxy_after_a_403(monkeypatch):
    calls = []

    def get(url, timeout):
        calls.append(url)
        if url.startswith("https://esoicons"):
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        if "gone" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return b"png"

    monkeypatch.setattr(uesp, "_get", get)
    monkeypatch.setattr(uesp, "_blocked_until", 0.0)
    assert uesp.fetch_png("https://esoicons.uesp.net/esoui/art/icons/a.png") == b"png"
    assert uesp.fetch_png("https://esoicons.uesp.net/esoui/art/icons/b.png") == b"png"  # straight to the proxy now
    assert uesp.fetch_png("https://esoicons.uesp.net/esoui/art/icons/gone.png") is None
    assert calls == [
        "https://esoicons.uesp.net/esoui/art/icons/a.png",
        "https://i0.wp.com/esoicons.uesp.net/esoui/art/icons/a.png",
        "https://i0.wp.com/esoicons.uesp.net/esoui/art/icons/b.png",
        "https://i0.wp.com/esoicons.uesp.net/esoui/art/icons/gone.png",
    ]


def test_uesp_served_directly_when_not_refused(monkeypatch):
    monkeypatch.setattr(uesp, "_get", lambda url, timeout: url.encode())
    monkeypatch.setattr(uesp, "_blocked_until", 0.0)
    assert uesp.fetch_png("https://images.uesp.net/2/26/x.png") == b"https://images.uesp.net/2/26/x.png"

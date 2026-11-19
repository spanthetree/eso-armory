"""Fetch game images from UESP, through a public image proxy when UESP refuses this host.

UESP sits behind Cloudflare, which answers many cloud hosts (AWS, Lightsail and others) with HTTP 403. WordPress.com's
Photon image CDN (i0.wp.com) is not refused, so after a 403 images come through it instead. Photon re-encodes PNGs
(sometimes to a 256-colour palette: on visible pixels about 1/255 off on average), so UESP is always tried first.
"""
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; eso-armory)"  # UESP rejects urllib's default agent
PNG = b"\x89PNG\r\n\x1a\n"
PROXY = "https://i0.wp.com/"  # Photon: https://i0.wp.com/<host>/<path>
BLOCK_BACKOFF = 600  # seconds to go straight to the proxy after UESP refused this host
MAX_BYTES = 8 * 1024 * 1024  # the largest image (a loading screen) is about 3 MB

_blocked_until = 0.0


def _get(url: str, timeout: float) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        body = r.read(MAX_BYTES)
    if not body.startswith(PNG):
        raise ValueError(f"not a PNG: {url}")
    return body


def fetch_png(url: str, timeout: float = 30) -> bytes | None:
    """PNG bytes of a UESP image, or None when it doesn't exist (404). Other failures raise."""
    global _blocked_until
    if time.monotonic() >= _blocked_until:
        try:
            return _get(url, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code != 403:
                raise
            _blocked_until = time.monotonic() + BLOCK_BACKOFF
    try:
        return _get(PROXY + url.split("://", 1)[-1], timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise

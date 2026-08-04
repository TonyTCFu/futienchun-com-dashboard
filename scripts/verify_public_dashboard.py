from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.request


def fetch(url: str) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "tw-dashboard-verify/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(), {key.lower(): value for key, value in response.headers.items()}


def normalized_version(value: str) -> str:
    return value.strip().removeprefix('W/').strip('"')


def verify_once(base_url: str, target_date: str) -> None:
    base_url = base_url.rstrip("/")
    home, home_headers = fetch(base_url + "/")
    healthz, _ = fetch(base_url + "/healthz")
    version_payload, _ = fetch(base_url + "/version.json")
    version = json.loads(version_payload.decode("utf-8"))
    digest = hashlib.sha256(home).hexdigest()
    public_version = str(version.get("version", ""))
    header_version = home_headers.get("x-dashboard-version", "")
    etag = home_headers.get("etag", "")
    text = home.decode("utf-8")
    required = (
        f"今日 Dashboard 更新日期：{target_date}",
        f"行情/回测序列最新日期：{target_date}",
    )
    missing = [fragment for fragment in required if fragment not in text]
    if healthz.decode("utf-8").strip() != "ok":
        raise RuntimeError("public /healthz is not ok")
    if missing:
        raise RuntimeError("public dashboard date mismatch: " + " | ".join(missing))
    if re.search(r'class="signal-pill sell"', text):
        raise RuntimeError("public dashboard still contains a sell signal pill")
    expected = {digest, public_version}
    if header_version and header_version not in expected:
        raise RuntimeError("X-Dashboard-Version does not match /version.json or homepage body")
    if normalized_version(etag) not in expected:
        raise RuntimeError("ETag does not match /version.json or homepage body")
    if digest != public_version:
        raise RuntimeError("homepage SHA-256 does not match /version.json")
    print(f"public_dashboard_verify_ok version={public_version} target_date={target_date}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify public Taiwan Dashboard content and cache version headers.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--delay", type=int, default=10)
    args = parser.parse_args()
    last_error: Exception | None = None
    for attempt in range(1, max(args.retries, 1) + 1):
        try:
            verify_once(args.url, args.target_date)
            return
        except Exception as exc:
            last_error = exc
            if attempt < args.retries:
                time.sleep(args.delay)
    raise SystemExit(f"public dashboard verification failed after {args.retries} attempts: {last_error}")


if __name__ == "__main__":
    main()

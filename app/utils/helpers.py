import json
import re
import secrets
import unicodedata
from typing import Any

from bleach import clean

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def generate_slug(first_name: str, last_name: str) -> str:
    base = f"{first_name}-{last_name}".lower()
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "card"
    suffix = secrets.token_hex(3)
    return f"{base}-{suffix}"


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except json.JSONDecodeError:
        pass
    return [s.strip() for s in value.split(",") if s.strip()]


def dump_json_list(items: list[str] | None) -> str | None:
    if not items:
        return None
    cleaned = [sanitize_text(i, max_len=500) for i in items if i and i.strip()]
    return json.dumps(cleaned) if cleaned else None


def parse_extra_links(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    try:
        data = json.loads(value)
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict) and item.get("label") and item.get("url"):
                    result.append({
                        "label": sanitize_text(str(item["label"]), 100),
                        "url": sanitize_url(str(item["url"])),
                    })
            return [x for x in result if x["url"]]
    except json.JSONDecodeError:
        pass
    return []


def dump_extra_links(links: list[dict[str, str]] | None) -> str | None:
    if not links:
        return None
    safe = []
    for link in links:
        url = sanitize_url(link.get("url", ""))
        label = sanitize_text(link.get("label", "Link"), 100)
        if url:
            safe.append({"label": label, "url": url})
    return json.dumps(safe) if safe else None


def sanitize_text(text: str, max_len: int = 10000) -> str:
    if not text:
        return ""
    cleaned = clean(text, tags=[], strip=True)
    return cleaned[:max_len].strip()


def sanitize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if url.startswith(("http://", "https://", "tel:", "mailto:")):
        return url[:500]
    if url.startswith("@"):
        return url[:100]
    if url.startswith("t.me/") or url.startswith("instagram.com"):
        return f"https://{url}"[:500]
    return f"https://{url}"[:500]


def hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    import hashlib
    salt = "neocard-analytics"
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()

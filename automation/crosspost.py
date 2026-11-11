#!/usr/bin/env python3
"""
Безкоштовне автоматичне промо: крос-пост останнього поста сайту в соцмережі.

Бере найсвіжіший запис із docs/rss.xml і публікує його в:
  • Bluesky   (BSKY_HANDLE + BSKY_APP_PASSWORD)
  • Mastodon  (MASTODON_BASE + MASTODON_TOKEN)

Кожен акаунт — 5 хвилин реєстрації, далі все йде автоматично.
Дублікати не публікуються: останній опублікований RSS-link зберігається
в automation/.crosspost-state.json.

Команди:
  python3 automation/crosspost.py            # опублікувати, якщо є нове
  python3 automation/crosspost.py --dry-run  # показати, що було б опубліковано

Додати в .env (рядки, які потрібні):
  BSKY_HANDLE=ім’я.bsky.social
  BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
  MASTODON_BASE=https://mastodon.social
  MASTODON_TOKEN=...
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
STATE_FILE = ROOT / "automation" / ".crosspost-state.json"
RSS_FILE = ROOT / "docs" / "rss.xml"

TAGS = "#українціВРимі #Рим #Італія"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def latest_post() -> tuple[str, str, str] | None:
    """Заголовок, посилання, короткий опис із найсвіжішого запису RSS."""
    if not RSS_FILE.exists():
        return None
    root = ET.parse(RSS_FILE).getroot()
    items = root.findall("./channel/item")
    if not items:
        return None

    def key(item: ET.Element) -> float:
        from email.utils import parsedate_to_datetime

        raw = (item.findtext("pubDate") or "").strip()
        try:
            return parsedate_to_datetime(raw).timestamp()
        except (TypeError, ValueError):
            return 0.0

    import time

    now = time.time()
    item = max(items, key=key)
    # Заплановані на майбутнє пости (їх ще немає в каналі) не крос-постимо.
    if key(item) > now:
        items = [it for it in items if key(it) <= now]
        if not items:
            return None
        item = max(items, key=key)
    title = (item.findtext("title") or "").strip()
    link = (item.findtext("link") or "").strip()
    desc = (item.findtext("description") or "").strip()
    return title, link, desc


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def http_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url, data=body, method="POST" if body else "GET",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def compose(title: str, link: str, desc: str, limit: int) -> str:
    desc_short = desc[:300].rsplit(" ", 1)[0] if len(desc) > 300 else desc
    text = f"{title}\n\n{desc_short}\n\n{link}\n{TAGS}"
    return text if len(text) <= limit else text[: limit - 1] + "…"


def post_bluesky(text: str, link: str) -> None:
    handle = os.environ.get("BSKY_HANDLE", "").strip()
    password = os.environ.get("BSKY_APP_PASSWORD", "").strip()
    if not handle or not password:
        print("  Bluesky: не налаштовано (BSKY_HANDLE / BSKY_APP_PASSWORD у .env)")
        return
    session = http_json(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        {"identifier": handle, "password": password},
    )
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat().replace("+00:00", "Z"),
        "facets": [
            {
                "index": {"byteStart": len((text[: text.find(link)]).encode("utf-8")),
                          "byteEnd": len((text[: text.find(link) + len(link)]).encode("utf-8"))},
                "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link}],
            }
        ] if link in text else [],
        "embed": {
            "$type": "app.bsky.embed.external",
            "external": {"uri": link, "title": "", "description": ""},
        },
    }
    # Заголовок/опис картки Bluesky підтягне сам із og-тегів сторінки.
    record["embed"]["external"].pop("title")
    record["embed"]["external"].pop("description")
    http_json(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        {"repo": session["did"], "collection": "app.bsky.feed.post", "record": record},
        {"Authorization": f"Bearer {session['accessJwt']}"},
    )
    print("  Bluesky: опубліковано")


def post_mastodon(text: str) -> None:
    base = os.environ.get("MASTODON_BASE", "").strip().rstrip("/")
    token = os.environ.get("MASTODON_TOKEN", "").strip()
    if not base or not token:
        print("  Mastodon: не налаштовано (MASTODON_BASE / MASTODON_TOKEN у .env)")
        return
    body = json.dumps({"status": text}).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/v1/statuses", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        json.loads(response.read().decode("utf-8"))
    print("  Mastodon: опубліковано")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    post = latest_post()
    if not post:
        sys.exit("Немає постів у docs/rss.xml — спершу python3 automation/site.py")
    title, link, desc = post
    state = load_state()

    pending = [net for net in ("bluesky", "mastodon") if state.get(net) != link]
    print(f"Останній пост RSS: {title}\n  {link}")
    if not pending:
        print("Усі мережі вже мають цей пост — нічого нового.")
        return

    bluesky_text = compose(title, link, desc, 300)
    mastodon_text = compose(title, link, desc, 480)
    if args.dry_run:
        print(f"\n[Bluesky]\n{bluesky_text}\n\n[Mastodon]\n{mastodon_text}")
        return

    if "bluesky" in pending:
        post_bluesky(bluesky_text, link)
        state["bluesky"] = link
    if "mastodon" in pending:
        post_mastodon(mastodon_text)
        state["mastodon"] = link
    save_state(state)


if __name__ == "__main__":
    main()

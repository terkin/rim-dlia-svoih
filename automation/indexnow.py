#!/usr/bin/env python3
"""
Подання URL сайту в IndexNow (Bing, Yandex, Seznam, Naver).

Перед запуском:
  1. python3 automation/site.py   — згенерує docs/ і ключ automation/indexnow.key
  2. Опублікуйте docs/ на GitHub Pages
  3. python3 automation/indexnow.py

Скрипт бере ключ із automation/indexnow.key, читає docs/sitemap.xml
і надсилає всі URL на https://api.indexnow.org/indexnow.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
KEY_FILE = ROOT / "automation/indexnow.key"
SITE_URL = os.environ.get("SITE_URL", "https://ucrainiroma.it").rstrip("/")
ENDPOINT = "https://api.indexnow.org/indexnow"


def load_key() -> str:
    if not KEY_FILE.exists():
        sys.exit("Немає automation/indexnow.key — спершу запустіть python3 automation/site.py")
    value = KEY_FILE.read_text(encoding="utf-8").strip()
    if not value:
        sys.exit("Порожній automation/indexnow.key")
    return value


def urls_from_sitemap() -> list[str]:
    path = DOCS / "sitemap.xml"
    if not path.exists():
        sys.exit("Немає docs/sitemap.xml — спершу запустіть python3 automation/site.py")
    xml = path.read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def main() -> None:
    key = load_key()
    urls = urls_from_sitemap()
    if not urls:
        sys.exit("У sitemap.xml немає URL")

    host = re.sub(r"^https?://", "", SITE_URL).split("/")[0]
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{SITE_URL}/{key}.txt",
        "urlList": urls,
    }

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    print(f"IndexNow → {ENDPOINT}")
    print(f"  host: {host}")
    print(f"  URLs: {len(urls)}")
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            print(f"  HTTP {response.status}")
            body = response.read().decode("utf-8", "replace")
            if body:
                print(f"  {body[:300]}")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        print(f"  HTTP {error.code}: {body[:300]}")
        if error.code == 403:
            print("  Перевірте, що файл ключа доступний за keyLocation.")
        sys.exit(1)
    except urllib.error.URLError as error:
        sys.exit(f"  Немає зв'язку: {error.reason}")


if __name__ == "__main__":
    main()

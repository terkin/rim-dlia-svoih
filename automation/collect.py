#!/usr/bin/env python3
"""
Збирає кандидатів на пости з RSS-джерел Риму.

Запуск:
    python3 automation/collect.py
    python3 automation/collect.py --limit 40

Результат: automation/candidates.json
Далі цей файл читає AI-редактор (draft.py) і робить із нього чернетки постів.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "candidates.json"

FEEDS = {
    "ANSA Lazio": "https://www.ansa.it/lazio/notizie/lazio_rss.xml",
    "Corriere Roma": "https://www.corriere.it/dynamic-feed/rss/section/Roma.xml",
    "Il Messaggero Roma": "https://www.ilmessaggero.it/rss/roma.xml",
    "Il Tempo": "https://www.iltempo.it/arc/outboundfeeds/rss/",
    "AGI": "https://www.agi.it/cronaca/rss.xml",
    "Adnkronos": "https://www.adnkronos.com/RSS_Ultimora.xml",
    "Il Sole 24 Ore": "https://www.ilsole24ore.com/rss/italia.xml",
    "Il Fatto Quotidiano": "https://www.ilfattoquotidiano.it/feed/",
}

# macOS/Homebrew Python іноді не бачить системні CA-сертифікати.
# Пробуємо стандартні шляхи, щоб RSS не падав із CERTIFICATE_VERIFY_FAILED.
CA_BUNDLES = (
    "/opt/homebrew/etc/openssl@3/cert.pem",
    "/usr/local/etc/openssl@3/cert.pem",
    "/etc/ssl/cert.pem",
)

# Слова, за якими розуміємо, що новина стосується Риму або життя в місті
KEYWORDS = [
    "roma", "romano", "lazio", "ostia", "trastevere", "esquilino", "prati",
    "testaccio", "san lorenzo", "pigneto", "monteverde", "eur", "casilina",
    "atac", "metro", "metropolitana", "trenitalia", "cotral", "bus", "tram",
    "comune", "municipio", "campidoglio", "regione lazio", "asl", "sanità",
    "affitto", "casa", "lavoro", "disoccupazione", "stipendio", "bolletta",
    "strada", "traffico", "incidente", "sciopero", "manifestazione",
    "sapienza", "tor vergata", "roma tre", "università", "scuola", "bambini",
]

USER_AGENT = "Mozilla/5.0 (compatible; RimDliaSvoihBot/1.0)"


def ssl_context() -> ssl.SSLContext | None:
    for bundle in CA_BUNDLES:
        if Path(bundle).exists():
            try:
                return ssl.create_default_context(cafile=bundle)
            except ssl.SSLError:
                continue
    return None


def fetch(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def clean(text: str | None, limit: int = 320) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_date(value: str | None) -> str:
    if not value:
        return ""
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return value.strip()


def items_from_feed(source: str, url: str) -> list[dict]:
    try:
        root = ET.fromstring(fetch(url))
    except Exception as error:  # noqa: BLE001
        print(f"  ! {source}: {error}", file=sys.stderr)
        return []

    # RSS 2.0 або Atom
    nodes = root.findall(".//item")
    if not nodes:
        nodes = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    result = []
    for node in nodes:
        def text(tag: str) -> str:
            for prefix in ("", "{http://www.w3.org/2005/Atom}"):
                found = node.find(prefix + tag)
                if found is not None and found.text:
                    return found.text
            return ""

        title = clean(text("title"), 240)
        link = text("link")
        if not link:
            link_node = node.find("{http://www.w3.org/2005/Atom}link")
            if link_node is not None:
                link = link_node.attrib.get("href", "")
        summary = clean(text("description") or text("summary") or text("content"), 320)
        published = parse_date(text("pubDate") or text("published") or text("updated"))
        if not title or not link:
            continue
        result.append(
            {
                "source": source,
                "title": title,
                "link": link.strip(),
                "published": published,
                "summary": summary,
            }
        )
    return result


def is_relevant(item: dict) -> bool:
    haystack = f"{item['title']} {item['summary']}".lower()
    return any(keyword in haystack for keyword in KEYWORDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=40, help="скільки кандидатів зберегти")
    parser.add_argument("--per-source", type=int, default=5, help="максимум новин з одного джерела")
    parser.add_argument("--all", action="store_true", help="не фільтрувати за ключовими словами")
    args = parser.parse_args()

    collected: list[dict] = []
    seen: set[str] = set()

    for source, url in FEEDS.items():
        print(f"→ {source}")
        for item in items_from_feed(source, url):
            if item["link"] in seen:
                continue
            if not args.all and not is_relevant(item):
                continue
            seen.add(item["link"])
            collected.append(item)

    collected.sort(key=lambda item: item["published"], reverse=True)

    # Не даємо одному джерелу забити весь список: спочатку по кілька новин
    # з кожного видання, потім — решта до ліміту.
    if args.per_source > 0:
        balanced: list[dict] = []
        counts: dict[str, int] = {}
        for item in collected:
            if counts.get(item["source"], 0) >= args.per_source:
                continue
            counts[item["source"]] = counts.get(item["source"], 0) + 1
            balanced.append(item)
            if len(balanced) >= args.limit:
                break
        collected = balanced
    else:
        collected = collected[: args.limit]

    OUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(collected),
                "items": collected,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nЗбережено {len(collected)} кандидатів → {OUT}")


if __name__ == "__main__":
    main()

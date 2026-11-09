#!/usr/bin/env python3
"""
Знімає публічну статистику каналу з t.me/s/<channel>:
перегляди, реакції, пересилання, текст і дату кожного поста.

Запуск:
    python3 automation/report.py
    python3 automation/report.py --json

Результат: automation/report.json + таблиця в консолі.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import publish  # noqa: E402

OUT = Path(__file__).resolve().parent / "report.json"
USER_AGENT = "Mozilla/5.0 (compatible; RimDliaSvoihBot/1.0)"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


def number(value: str) -> int:
    digits = re.sub(r"[^\d]", "", value or "")
    return int(digits) if digits else 0


def parse_channel(channel: str) -> dict:
    handle = channel.lstrip("@")
    page = fetch(f"https://t.me/s/{handle}")
    chunks = page.split('class="tgme_widget_message_wrap')[1:]

    posts = []
    for chunk in chunks:
        match = re.search(r'data-post="[^/]+/(\d+)"', chunk)
        if not match:
            continue
        if "service_message" in chunk:
            continue
        message_id = int(match.group(1))

        text_match = re.search(
            r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', chunk, re.S
        )
        text = strip_tags(text_match.group(1)) if text_match else ""

        views_match = re.search(
            r'class="tgme_widget_message_views">([^<]+)<', chunk
        )
        views = number(views_match.group(1)) if views_match else 0

        date_match = re.search(r'<time[^>]+datetime="([^"]+)"', chunk)
        date = date_match.group(1) if date_match else ""

        reactions = len(re.findall(r'class="tgme_reaction"', chunk))
        forwards_match = re.search(
            r'class="tgme_widget_message_forwards[^"]*"[^>]*>.*?([\d\s.,KkMm]+)',
            chunk,
            re.S,
        )
        forwards = number(forwards_match.group(1)) if forwards_match else 0

        posts.append(
            {
                "message_id": message_id,
                "date": date,
                "views": views,
                "reactions": reactions,
                "forwards": forwards,
                "has_photo": "tgme_widget_message_photo_wrap" in chunk,
                "text": text,
                "preview": text.replace("\n", " ")[:90],
            }
        )

    posts.sort(key=lambda item: item["message_id"])
    content_posts = [post for post in posts if post["text"] or post["has_photo"]]
    total_views = sum(post["views"] for post in content_posts)
    return {
        "channel": handle,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "posts": posts,
        "content_posts": len(content_posts),
        "total_views": total_views,
        "average_views": round(total_views / len(content_posts)) if content_posts else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="вивести JSON")
    args = parser.parse_args()

    publish.load_env()
    data = parse_channel(publish.channel())
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print(f"Канал: @{data['channel']}")
    print(f"Постів із контентом: {data['content_posts']}")
    print(f"Середні перегляди: {data['average_views']}")
    print()
    print(f"{'ID':>4}  {'Views':>6}  {'React':>5}  {'Photo':>5}  Текст")
    print("-" * 78)
    for post in data["posts"]:
        if not (post["text"] or post["has_photo"]):
            continue
        photo = "yes" if post["has_photo"] else "no"
        print(
            f"{post['message_id']:>4}  {post['views']:>6}  {post['reactions']:>5}  "
            f"{photo:>5}  {post['preview'][:46]}"
        )
    print(f"\nЗбережено → {OUT}")


if __name__ == "__main__":
    main()

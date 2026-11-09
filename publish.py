#!/usr/bin/env python3
"""
Публікація постів у Telegram-канал «Рим для своїх» через Bot API.

Підготовка (один раз):
  1. Створіть бота в @BotFather → отримайте токен.
  2. Додайте бота адміністратором каналу з правами:
     Post messages, Edit messages, Change channel info.
  3. Створіть файл .env поруч із цим скриптом:
        TELEGRAM_BOT_TOKEN=123456:ABC...
        TELEGRAM_CHANNEL=@rim_dlia_svoih
     і виконайте: chmod 600 .env

Команди:
  python3 publish.py check
  python3 publish.py setup
  python3 publish.py pinned
  python3 publish.py post 3
  python3 publish.py all
  python3 publish.py pin 123
  python3 publish.py post 3 --dry-run

Токен нікуди не надсилається, крім api.telegram.org.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
DEFAULT_CHANNEL = "@rim_dlia_svoih"

# 0-based індекси постів → обкладинки (тепер є в кожного поста)
COVERS = {
    0: ROOT / "covers/2026-11-09-intro.png",
    1: ROOT / "covers/2026-11-10-transport.png",
    2: ROOT / "covers/2026-11-11-kids.png",
    3: ROOT / "covers/2026-11-12-exhibitions.png",
    4: ROOT / "covers/2026-11-13-money.png",
    5: ROOT / "covers/2026-11-14-weekend.png",
    6: ROOT / "covers/2026-11-15-digest.png",
}

DESCRIPTION = (
    "Щотижневий дайджест для українців у Римі: події, транспорт, житло, "
    "робота, здоров'я, безпека. Без паніки, з джерелами. 🇺🇦🇮🇹"
)


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def token() -> str:
    value = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not value:
        sys.exit(
            "Немає TELEGRAM_BOT_TOKEN. Створіть .env поруч зі скриптом:\n"
            "  TELEGRAM_BOT_TOKEN=123456:ABC...\n"
            "  TELEGRAM_CHANNEL=@rim_dlia_svoih"
        )
    return value


def channel() -> str:
    return os.environ.get("TELEGRAM_CHANNEL", DEFAULT_CHANNEL).strip()


def api(method: str, params: dict | None = None, files: dict | None = None):
    url = f"https://api.telegram.org/bot{token()}/{method}"
    if files:
        boundary = uuid.uuid4().hex
        body = bytearray()
        for key, value in (params or {}).items():
            body += (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        for key, (filename, data, ctype) in files.items():
            body += (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n"
            ).encode("utf-8")
            body += data + b"\r\n"
        body += f"--{boundary}--\r\n".encode("utf-8")
        request = urllib.request.Request(
            url,
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
    else:
        request = urllib.request.Request(
            url,
            data=json.dumps(params or {}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except Exception:
            sys.exit(f"HTTP {error.code}: {error.reason}")
        sys.exit(f"Telegram error: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    except urllib.error.URLError as error:
        sys.exit(f"Немає зв'язку з api.telegram.org: {error.reason}")

    if not payload.get("ok"):
        sys.exit(f"Telegram error: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    return payload["result"]


def code_blocks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [block.strip("\n") for block in re.findall(r"```\n(.*?)\n```", text, re.S)]


def first_week_posts() -> list[str]:
    return code_blocks(ROOT / "content/01-first-week.md")


def pinned_post() -> str:
    blocks = code_blocks(ROOT / "content/00-pinned-post.md")
    if not blocks:
        sys.exit("Не знайдено текст закріпленого поста.")
    return blocks[0]


def html_caption(text: str) -> str:
    """Екранує HTML і робить перший рядок жирним."""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = escaped.split("\n")
    for index, line in enumerate(lines):
        if line.strip():
            lines[index] = f"<b>{line}</b>"
            break
    return "\n".join(lines)


def send_text(text: str, dry_run: bool) -> int:
    if dry_run:
        print(f"  [dry-run] sendMessage · {len(text)} символів")
        return 0
    result = api(
        "sendMessage",
        {
            "chat_id": channel(),
            "text": html_caption(text),
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        },
    )
    return result["message_id"]


def send_photo(text: str, image: Path, dry_run: bool) -> int:
    if dry_run:
        print(f"  [dry-run] sendPhoto · {image.name} · підпис {len(text)} символів")
        return 0
    if len(text) > 1024:
        sys.exit(f"Підпис {len(text)} символів — більше ліміту 1024.")
    data = image.read_bytes()
    result = api(
        "sendPhoto",
        {
            "chat_id": channel(),
            "caption": html_caption(text),
            "parse_mode": "HTML",
        },
        files={"photo": (image.name, data, "image/png")},
    )
    return result["message_id"]


def cmd_check(args) -> None:
    me = api("getMe")
    print(f"Бот: @{me.get('username')} ({me.get('first_name')})")
    chat = api("getChat", {"chat_id": channel()})
    print(f"Канал: {chat.get('title')} · @{chat.get('username')} · id={chat.get('id')}")
    print(f"Опис: {chat.get('description') or '—'}")
    print(f"Аватар: {'є' if chat.get('photo') else 'немає'}")
    member = api("getChatMember", {"chat_id": channel(), "user_id": me["id"]})
    print(f"Статус бота: {member.get('status')}")
    if member.get("status") not in ("administrator", "creator"):
        print("⚠️  Бот не адміністратор — публікація не працюватиме.")


def cmd_setup(args) -> None:
    api("setChatDescription", {"chat_id": channel(), "description": DESCRIPTION})
    print(f"Опис оновлено ({len(DESCRIPTION)} символів).")
    if args.skip_photo:
        return
    image = ROOT / "brand/avatar.png"
    result = api(
        "setChatPhoto",
        {"chat_id": channel()},
        files={"photo": (image.name, image.read_bytes(), "image/png")},
    )
    print(f"Аватар оновлено: {image.name}")


def cmd_pinned(args) -> None:
    text = pinned_post()
    image = ROOT / "brand/avatar.png"
    if args.text_only:
        message_id = send_text(text, args.dry_run)
    else:
        message_id = send_photo(text, image, args.dry_run)
    print(f"Закріплений пост: message_id={message_id}")
    if not args.dry_run and not args.no_pin:
        api(
            "pinChatMessage",
            {"chat_id": channel(), "message_id": message_id, "disable_notification": True},
        )
        print("Закріплено.")


def cmd_post(args) -> None:
    posts = first_week_posts()
    number = args.number
    if not 1 <= number <= len(posts):
        sys.exit(f"Є лише {len(posts)} постів (1–{len(posts)}).")
    index = number - 1
    text = posts[index]
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    print(f"Пост {number}: {len(text)} символів · {first_line[:60]}")
    cover = COVERS.get(index)
    if cover and cover.exists():
        message_id = send_photo(text, cover, args.dry_run)
    else:
        message_id = send_text(text, args.dry_run)
    print(f"  message_id={message_id}")


def cmd_all(args) -> None:
    posts = first_week_posts()
    print(f"Публікую {len(posts)} постів у {channel()}…")
    for number in range(1, len(posts) + 1):
        print(f"\n[{number}/{len(posts)}]")
        cmd_post(argparse.Namespace(number=number, dry_run=args.dry_run))


def cmd_text(args) -> None:
    path = Path(args.file)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        sys.exit(f"Немає файлу: {path}")
    text = path.read_text(encoding="utf-8").strip()
    print(f"Текст: {len(text)} символів · {path.name}")
    message_id = send_text(text, args.dry_run)
    print(f"  message_id={message_id}")


def cmd_pin(args) -> None:
    if args.dry_run:
        print(f"  [dry-run] pinChatMessage · message_id={args.message_id}")
        return
    api(
        "pinChatMessage",
        {
            "chat_id": channel(),
            "message_id": args.message_id,
            "disable_notification": True,
        },
    )
    print(f"Закріплено message_id={args.message_id}")


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Публікація в Telegram-канал «Рим для своїх»")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="перевірити бота, канал і права")
    p_check.set_defaults(func=cmd_check)

    p_setup = sub.add_parser("setup", help="поставити опис і аватар")
    p_setup.add_argument("--skip-photo", action="store_true")
    p_setup.set_defaults(func=cmd_setup)

    p_pinned = sub.add_parser("pinned", help="опублікувати й закріпити пост-знайомство")
    p_pinned.add_argument("--text-only", action="store_true")
    p_pinned.add_argument("--no-pin", action="store_true")
    p_pinned.add_argument("--dry-run", action="store_true")
    p_pinned.set_defaults(func=cmd_pinned)

    p_post = sub.add_parser("post", help="опублікувати один пост тижня")
    p_post.add_argument("number", type=int, choices=range(1, 8))
    p_post.add_argument("--dry-run", action="store_true")
    p_post.set_defaults(func=cmd_post)

    p_all = sub.add_parser("all", help="опублікувати всі 7 постів")
    p_all.add_argument("--dry-run", action="store_true")
    p_all.set_defaults(func=cmd_all)

    p_text = sub.add_parser("text", help="опублікувати текст із файлу")
    p_text.add_argument("file", help="шлях до .txt або .md з текстом")
    p_text.add_argument("--dry-run", action="store_true")
    p_text.set_defaults(func=cmd_text)

    p_pin = sub.add_parser("pin", help="закріпити повідомлення за message_id")
    p_pin.add_argument("message_id", type=int)
    p_pin.add_argument("--dry-run", action="store_true")
    p_pin.set_defaults(func=cmd_pin)

    args = parser.parse_args()
    if getattr(args, "dry_run", False):
        # dry-run не потребує токена
        os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dry-run")
    args.func(args)


if __name__ == "__main__":
    main()

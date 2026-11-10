#!/usr/bin/env python3
"""
Генератор статичного SEO-сайту для каналу «Рим для своїх».

Створює в docs/:
  index.html          — головна сторінка
  posts/<slug>.html   — окрема сторінка кожного поста
  covers/*.png        — копії обкладинок
  sitemap.xml
  robots.txt
  rss.xml
  404.html
  <indexnow-key>.txt  — файл підтвердження IndexNow

Запуск:
  python3 automation/site.py
  SITE_URL=https://example.com python3 automation/site.py
"""
from __future__ import annotations

import html
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
COVERS = ROOT / "covers"
CONTENT = ROOT / "content/01-first-week.md"
EXTRA = ROOT / "content/extra"
KEY_FILE = ROOT / "automation/indexnow.key"

SITE_URL = os.environ.get("SITE_URL", "https://ucrainiroma.it").rstrip("/")
CHANNEL_URL = "https://t.me/rim_dlia_svoih"
CHANNEL_HANDLE = "@rim_dlia_svoih"
CHANNEL_TITLE = "Рим для своїх | Українці в Римі"
CHANNEL_DESC = (
    "Щотижневий дайджест для українців у Римі: події, транспорт, житло, "
    "робота, здоров'я, безпека. Без паніки, з джерелами. 🇺🇦🇮🇹"
)
CHANNEL_DESC_IT = (
    "Digest settimanale per gli ucraini a Roma: eventi, trasporti, casa, "
    "lavoro, salute, sicurezza. Senza allarmismi, con le fonti. 🇺🇦🇮🇹"
)

# Перекладений контент: content/it/<slug>.md (той самий slug, що й обкладинка)
IT_CONTENT = ROOT / "content/it"

LANGS = ("uk", "it")

BRAND = {"uk": "Рим для своїх", "it": "Rim per i nostri"}
SITE_NAME = {"uk": CHANNEL_TITLE, "it": "Rim per i nostri | Ucraini a Roma"}
LOCALE = {"uk": "uk_UA", "it": "it_IT"}
FOOTER = {
    "uk": "© 2026 «Рим для своїх». Незалежний дайджест для українців у Римі.",
    "it": "© 2026 «Rim per i nostri». Digest indipendente per gli ucraini a Roma.",
}

TOPICS = {
    "uk": [
        ("🗓", "Події та виставки", "Куди піти цього тижня: безкоштовні події, виставки, що закриваються, ярмарки."),
        ("🚇", "Транспорт", "Страйки, ремонти, закриття станцій, зміни маршрутів Roma-Lido, метро й автобусів."),
        ("🏠", "Житло й робота", "Оренда без посередників, вакансії, курси італійської, легальне працевлаштування."),
        ("🏥", "Здоров'я", "Лікарі, аналізи, SSN, невідкладна допомога, де шукати україномовного лікаря."),
        ("⚠️", "Безпека", "Шахрайство, фішинг, райони, що робити в складній ситуації."),
        ("🇺🇦", "Україна і світ", "Коротко про головне — без паніки й без клікбейту."),
    ],
    "it": [
        ("🗓", "Eventi e mostre", "Dove andare questa settimana: eventi gratuiti, mostre in chiusura, mercatini."),
        ("🚇", "Trasporti", "Scioperi, cantieri, stazioni chiuse, cambi di percorso su Roma-Lido, metro e bus."),
        ("🏠", "Casa e lavoro", "Affitti senza intermediari, offerte di lavoro, corsi di italiano, lavoro regolare."),
        ("🏥", "Salute", "Medici, analisi, SSN, pronto soccorso e dove trovare un medico che parli ucraino."),
        ("⚠️", "Sicurezza", "Truffe, phishing, zone da conoscere e cosa fare in una situazione difficile."),
        ("🇺🇦", "Ucraina e mondo", "L'essenziale in breve: senza allarmismi e senza clickbait."),
    ],
}

STEPS = {
    "uk": [
        ("1", "Відкрийте канал", "Натисніть кнопку «Відкрити в Telegram» — канал публічний, читати можна без акаунта у вебверсії."),
        ("2", "Підпишіться", "Один дайджест на тиждень. Нічого зайвого: лише те, що стосується життя в Римі."),
        ("3", "Повертайтеся", "Якщо загубили пост — усі матеріали зібрані на цьому сайті."),
    ],
    "it": [
        ("1", "Apri il canale", "Premi «Apri in Telegram»: il canale è pubblico, si legge anche senza account nella versione web."),
        ("2", "Iscriviti", "Un digest a settimana. Niente di superfluo: solo ciò che riguarda la vita a Roma."),
        ("3", "Torna quando vuoi", "Se hai perso un post, tutti i materiali sono raccolti su questo sito."),
    ],
}

FAQ = {
    "uk": [
        ("Це офіційний канал?", "Ні. Це незалежний дайджест для українців, які нещодавно переїхали до Риму. Ми не установа й не посередник."),
        ("Скільки коштує підписка?", "Нічого. Канал безкоштовний, без реклами й без платних підписок."),
        ("Звідки беруться новини?", "З відкритих джерел: ANSA, Corriere Roma, Il Messaggero, Il Tempo, AGI, Adnkronos, Il Sole 24 Ore, Il Fatto Quotidiano та офіційних сайтів."),
        ("Чи можна писати вам?", "Так, у коментарях під постами. Питання й пропозиції допомагають робити дайджест кориснішим."),
    ],
    "it": [
        ("È un canale ufficiale?", "No. È un digest indipendente per gli ucraini arrivati da poco a Roma. Non siamo un ente né un intermediario."),
        ("Quanto costa l'iscrizione?", "Niente. Il canale è gratuito, senza pubblicità e senza abbonamenti."),
        ("Da dove arrivano le notizie?", "Da fonti aperte: ANSA, Corriere Roma, Il Messaggero, Il Tempo, AGI, Adnkronos, Il Sole 24 Ore, Il Fatto Quotidiano e siti istituzionali."),
        ("Si può scrivervi?", "Sì, nei commenti sotto i post. Domande e proposte aiutano a rendere il digest più utile."),
    ],
}

TEXT = {
    "uk": {
        "badge": "🇺🇦🇮🇹 Телеграм-канал для українців у Римі",
        "h1": "Рим для своїх — щотижневий дайджест для українців у Римі",
        "lead": "Події, транспорт, житло, робота, здоров'я й безпека. Коротко, з джерелами, без паніки. Для тих, хто нещодавно переїхав до Риму або вже живе тут.",
        "cta": "Відкрити в Telegram →",
        "cta2": "Останні пости",
        "meta": ["📅 Один дайджест на тиждень", "🔗 Джерела в кожному пості", "🆓 Безкоштовно"],
        "topics_h2": "Що всередині",
        "topics_sub": "Шість рубрик, які закривають перші місяці життя в Римі.",
        "posts_h2": "Останні пости",
        "posts_sub": "Ті самі матеріали, що виходять у каналі — зручно читати й пересилати.",
        "read": "Читати →",
        "how_h2": "Як це працює",
        "how_sub": "Три кроки — і ви нічого не пропустите.",
        "faq_h2": "Часті питання",
        "faq_sub": "Коротко про формат і правила.",
        "band_h2": "Приєднуйтеся до «Рим для своїх»",
        "band_p": "Щотижня — найважливіше для українців у Римі. Без паніки, з джерелами.",
        "home": "Головна",
        "posts_crumb": "Пости",
        "read_tg": "Читати в Telegram →",
        "nav_topics": "Теми",
        "nav_posts": "Пости",
        "nav_faq": "Питання",
        "nav_tg": "Telegram",
        "switch": "Italiano",
        "only_translated": "Інші пости доступні українською.",
        "title_index": "Рим для своїх — телеграм-канал для українців у Римі",
        "desc_index": "Щотижневий дайджест для українців у Римі: події, транспорт, житло, робота, здоров'я, безпека. Без паніки, з джерелами.",
    },
    "it": {
        "badge": "🇺🇦🇮🇹 Canale Telegram per gli ucraini a Roma",
        "h1": "Ucraini a Roma — il digest settimanale in italiano",
        "lead": "Eventi, trasporti, casa, lavoro, salute e sicurezza. In breve, con le fonti, senza allarmismi. Per chi è arrivato da poco a Roma o ci vive già.",
        "cta": "Apri in Telegram →",
        "cta2": "Ultimi post",
        "meta": ["📅 Un digest a settimana", "🔗 Fonti in ogni post", "🆓 Gratuito"],
        "topics_h2": "Di cosa parliamo",
        "topics_sub": "Sei rubriche che coprono i primi mesi di vita a Roma.",
        "posts_h2": "Ultimi post",
        "posts_sub": "Gli stessi materiali del canale — comodi da leggere e inoltrare.",
        "read": "Leggi →",
        "how_h2": "Come funziona",
        "how_sub": "Tre passi e non perdi niente.",
        "faq_h2": "Domande frequenti",
        "faq_sub": "In breve: formato e regole.",
        "band_h2": "Unisciti a «Rim per i nostri»",
        "band_p": "Ogni settimana l'essenziale per gli ucraini a Roma. Senza allarmismi, con le fonti.",
        "home": "Home",
        "posts_crumb": "Post",
        "read_tg": "Leggi in Telegram →",
        "nav_topics": "Temi",
        "nav_posts": "Post",
        "nav_faq": "Domande",
        "nav_tg": "Telegram",
        "switch": "Українська",
        "only_translated": "Gli altri post sono disponibili in ucraino.",
        "title_index": "Ucraini a Roma — eventi, trasporti, casa e lavoro | Rim per i nostri",
        "desc_index": "Digest settimanale per gli ucraini a Roma: eventi, trasporti, affitti, lavoro, salute e sicurezza. Con le fonti, senza allarmismi.",
    },
}

MONTHS = {
    1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
    5: "травня", 6: "червня", 7: "липня", 8: "серпня",
    9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня",
}


def code_blocks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [block.strip("\n") for block in re.findall(r"```\n(.*?)\n```", text, re.S)]


def extra_stems() -> set[str]:
    return {path.stem for path in EXTRA.glob("*.md")}


def cover_files() -> list[Path]:
    planned = extra_stems()
    return [path for path in sorted(COVERS.glob("2026-*.png")) if path.stem not in planned]


def slug_from_cover(cover: Path) -> str:
    return cover.stem


def post_date(cover: Path) -> datetime:
    return datetime.strptime(cover.name[:10], "%Y-%m-%d")


def human_date(value: datetime) -> str:
    return f"{value.day} {MONTHS[value.month]} {value.year}"


def first_line(text: str) -> str:
    line = next((line.strip() for line in text.splitlines() if line.strip()), "Без назви")
    return line.replace("**", "")


def excerpt(text: str, limit: int = 180) -> str:
    body = " ".join(line.strip() for line in text.splitlines() if line.strip()).replace("**", "")
    if len(body) <= limit:
        return body
    cut = body[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def body_excerpt(text: str, limit: int = 180) -> str:
    """Опис без першого рядка-заголовка (щоб не дублювати h1)."""
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip():
            start = i + 1
            break
    return excerpt("\n".join(lines[start:]), limit)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def paragraphs(text: str) -> str:
    """Перший рядок — жирний, решта — як є, зі збереженням переносів.

    Підтримує **жирний** усередині рядка (markdown-файли з content/extra).
    """
    lines = text.splitlines()
    out: list[str] = []
    first_done = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(line))
        if not first_done and "<strong>" not in safe:
            out.append(f"<strong>{safe}</strong>")
        else:
            out.append(safe)
        first_done = True
    return "\n".join(out)


def italian_texts() -> dict[str, str]:
    """Переклади постів: content/it/<slug>.md → текст."""
    if not IT_CONTENT.exists():
        return {}
    return {
        path.stem: path.read_text(encoding="utf-8").strip()
        for path in sorted(IT_CONTENT.glob("*.md"))
        if path.read_text(encoding="utf-8").strip()
    }


def load_posts() -> list[dict]:
    texts = code_blocks(CONTENT)
    covers = cover_files()
    if len(texts) != len(covers):
        raise SystemExit(
            f"Постів {len(texts)}, обкладинок {len(covers)} — кількість має збігатися."
        )
    translations = italian_texts()
    posts = []
    for text, cover in zip(texts, covers):
        posts.append(make_post(text, cover, translations.get(cover.stem)))
    posts.extend(extra_posts(translations))
    posts.sort(key=lambda post: (post["date"], post["slug"]))
    unknown = set(translations) - {post["slug"] for post in posts}
    if unknown:
        raise SystemExit(
            "Переклад без відповідного поста: " + ", ".join(sorted(unknown))
        )
    return posts


def make_post(text: str, cover: Path, text_it: str | None = None) -> dict:
    slug = slug_from_cover(cover)
    post = {
        "text": text,
        "cover": cover,
        "slug": slug,
        "date": post_date(cover),
        "title": first_line(text),
        "excerpt": body_excerpt(text),
        "url": f"{SITE_URL}/posts/{slug}.html",
        "text_it": text_it or "",
        "title_it": first_line(text_it) if text_it else "",
        "excerpt_it": body_excerpt(text_it) if text_it else "",
        "url_it": f"{SITE_URL}/it/posts/{slug}.html",
    }
    return post


def extra_posts(translations: dict[str, str] | None = None) -> list[dict]:
    """Окремі пости з content/extra/<slug>.md + covers/<slug>.png."""
    translations = translations or {}
    posts = []
    for path in sorted(EXTRA.glob("*.md")):
        cover = COVERS / f"{path.stem}.png"
        if not cover.exists():
            raise SystemExit(f"Немає обкладинки {cover.name} для content/extra/{path.name}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        posts.append(make_post(text, cover, translations.get(path.stem)))
    return posts


CSS = """
:root{
  --bg:#faf7f2;--paper:#fff;--ink:#1c1917;--ink2:#57534e;--line:#e7e1d8;
  --accent:#b45309;--accent2:#0f766e;--ua:#0057b7;--ua2:#ffd700;
  --radius:14px;--shadow:0 1px 2px rgba(28,25,23,.06),0 8px 24px rgba(28,25,23,.06);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
img{max-width:100%;display:block}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
header.site{border-bottom:1px solid var(--line);background:rgba(250,247,242,.9);backdrop-filter:blur(8px);position:sticky;top:0;z-index:10}
header.site .wrap{display:flex;align-items:center;gap:12px;min-height:64px}
header.site img{width:38px;height:38px;border-radius:50%}
header.site .brand{font-weight:700;letter-spacing:-.01em}
header.site nav{margin-left:auto;display:flex;gap:18px;font-size:14px}
header.site nav a{color:var(--ink2)}
header.site nav a.lang{color:var(--accent);font-weight:700}
.hero{padding:64px 0 40px}
.hero .badge{display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:600;
  background:#fff7ed;color:#9a3412;border:1px solid #fed7aa;padding:6px 12px;border-radius:999px}
.hero h1{font-size:clamp(30px,5vw,52px);line-height:1.1;letter-spacing:-.03em;margin:18px 0 16px}
.hero p.lead{font-size:clamp(17px,2.2vw,20px);color:var(--ink2);max-width:640px;margin:0 0 26px}
.cta{display:inline-flex;align-items:center;gap:10px;background:var(--ua);color:#fff;
  padding:14px 22px;border-radius:12px;font-weight:700;box-shadow:var(--shadow)}
.cta:hover{text-decoration:none;filter:brightness(1.08)}
.cta.secondary{background:var(--paper);color:var(--ink);border:1px solid var(--line)}
.hero .meta{display:flex;flex-wrap:wrap;gap:18px;margin-top:22px;color:var(--ink2);font-size:14px}
.hero .meta span{display:inline-flex;gap:6px;align-items:center}
section{padding:44px 0}
section h2{font-size:clamp(22px,3vw,30px);letter-spacing:-.02em;margin:0 0 8px}
section .sub{color:var(--ink2);margin:0 0 26px;max-width:620px}
.grid{display:grid;gap:16px}
.topics{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.card{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:22px;box-shadow:var(--shadow)}
.card .icon{font-size:24px;line-height:1}
.card h3{margin:10px 0 6px;font-size:17px}
.card p{margin:0;color:var(--ink2);font-size:14.5px}
.posts{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.post{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column}
.post img{aspect-ratio:4/3;object-fit:cover;width:100%}
.post .body{padding:16px 18px 20px;display:flex;flex-direction:column;gap:8px;flex:1}
.post time{font-size:13px;color:var(--ink2)}
.post h3{margin:0;font-size:16.5px;line-height:1.35}
.post p{margin:0;color:var(--ink2);font-size:14px}
.post .more{margin-top:auto;font-size:14px;font-weight:600}
.steps{grid-template-columns:repeat(auto-fit,minmax(220px,1fr));counter-reset:s}
.step{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:22px}
.step .n{display:inline-flex;width:34px;height:34px;align-items:center;justify-content:center;
  border-radius:50%;background:#ecfdf5;color:var(--accent2);font-weight:800}
.step h3{margin:12px 0 6px;font-size:16px}
.step p{margin:0;color:var(--ink2);font-size:14.5px}
.faq{display:grid;gap:10px;max-width:760px}
details{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
details summary{cursor:pointer;font-weight:600}
details p{margin:10px 0 0;color:var(--ink2)}
.band{background:#0b3b8c;color:#fff;border-radius:18px;padding:38px 30px;display:flex;flex-wrap:wrap;gap:22px;align-items:center;justify-content:space-between}
.band h2{margin:0 0 6px;color:#fff}
.band p{margin:0;color:#dbeafe}
.band .cta{background:var(--ua2);color:#1c1917}
footer.site{border-top:1px solid var(--line);padding:30px 0;color:var(--ink2);font-size:14px}
footer.site .wrap{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between}
.post-page{padding:40px 0 60px}
.post-page .crumbs{font-size:14px;color:var(--ink2);margin-bottom:18px}
.post-page h1{font-size:clamp(26px,4vw,40px);line-height:1.15;letter-spacing:-.02em;margin:0 0 10px}
.post-page time{color:var(--ink2);font-size:14px}
.post-page .cover{border-radius:var(--radius);overflow:hidden;border:1px solid var(--line);margin:24px 0;box-shadow:var(--shadow)}
.post-text{white-space:pre-wrap;background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:24px;font-size:16.5px;line-height:1.7;box-shadow:var(--shadow)}
.post-text strong{font-size:1.06em}
.pager{display:flex;justify-content:space-between;gap:16px;margin-top:24px;font-size:14px}
.skip{position:absolute;left:-9999px}
@media(max-width:640px){header.site nav{display:none}.hero{padding-top:44px}}
"""


def page_shell(
    title: str,
    description: str,
    canonical: str,
    body: str,
    extra_head: str = "",
    image: str | None = None,
    lang: str = "uk",
    alts: list[tuple[str, str]] | None = None,
    switch: tuple[str, str] | None = None,
) -> str:
    og_image = image or f"{SITE_URL}/covers/2026-11-09-intro.png"
    t = TEXT[lang]
    base = SITE_URL if lang == "uk" else f"{SITE_URL}/it"
    alts = alts or []
    hreflang = "".join(
        f'<link rel="alternate" hreflang="{code}" href="{esc(url)}">\n'
        for code, url in alts
    )
    switch_link = (
        f'<a class="lang" href="{esc(switch[0])}" hreflang="{esc(switch[1])}">{esc(t["switch"])}</a>'
        if switch
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{hreflang}<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME[lang])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{og_image}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{og_image}">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_NAME[lang])}" href="{SITE_URL}/rss.xml">
<link rel="icon" type="image/png" href="{SITE_URL}/avatar.png">
<style>{CSS}</style>
{extra_head}
</head>
<body>
<a class="skip" href="#main">{"Перейти до змісту" if lang == "uk" else "Vai al contenuto"}</a>
<header class="site">
  <div class="wrap">
    <img src="{SITE_URL}/avatar.png" alt="{esc(BRAND[lang])}" width="38" height="38">
    <span class="brand">{esc(BRAND[lang])}</span>
    <nav>
      <a href="{base}/#topics">{esc(t["nav_topics"])}</a>
      <a href="{base}/#posts">{esc(t["nav_posts"])}</a>
      <a href="{base}/#faq">{esc(t["nav_faq"])}</a>
      <a href="{CHANNEL_URL}" rel="noopener">{esc(t["nav_tg"])}</a>
      {switch_link}
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site">
  <div class="wrap">
    <span>{esc(FOOTER[lang])}</span>
    <span><a href="{CHANNEL_URL}" rel="noopener">t.me/rim_dlia_svoih</a> · <a href="{SITE_URL}/rss.xml">RSS</a></span>
  </div>
</footer>
</body>
</html>
"""


def org_schema() -> str:
    return (
        '{"@context":"https://schema.org","@type":"Organization",'
        f'"name":{json_str("Рим для своїх")},'
        f'"url":{json_str(SITE_URL)},'
        f'"sameAs":[{json_str(CHANNEL_URL)}],'
        f'"description":{json_str(CHANNEL_DESC)},'
        f'"logo":{json_str(SITE_URL + "/avatar.png")}'
        "}"
    )


def json_str(value: str) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


MONTHS_IT = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
    5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
    9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre",
}


def human_date_lang(value: datetime, lang: str) -> str:
    if lang == "it":
        return f"{value.day} {MONTHS_IT[value.month]} {value.year}"
    return human_date(value)


def index_page(posts: list[dict], lang: str = "uk") -> str:
    import json

    t = TEXT[lang]
    shown = [p for p in posts if lang == "uk" or p["text_it"]]
    cards = "\n".join(
        f"""<article class="post">
  <a href="{(p['url'] if lang == 'uk' else p['url_it'])}"><img src="{SITE_URL}/covers/{p['cover'].name}" alt="{esc(p['title'] if lang == 'uk' else p['title_it'])}" loading="lazy" width="640" height="480"></a>
  <div class="body">
    <time datetime="{p['date'].strftime('%Y-%m-%d')}">{human_date_lang(p['date'], lang)}</time>
    <h3><a href="{(p['url'] if lang == 'uk' else p['url_it'])}">{esc(p['title'] if lang == 'uk' else p['title_it'])}</a></h3>
    <p>{esc(p['excerpt'] if lang == 'uk' else p['excerpt_it'])}</p>
    <a class="more" href="{(p['url'] if lang == 'uk' else p['url_it'])}">{t['read']}</a>
  </div>
</article>"""
        for p in reversed(shown)
    )

    topics = "\n".join(
        f"""<div class="card">
  <div class="icon" aria-hidden="true">{icon}</div>
  <h3>{esc(title)}</h3>
  <p>{esc(text)}</p>
</div>"""
        for icon, title, text in TOPICS[lang]
    )

    steps = "\n".join(
        f"""<div class="step">
  <span class="n" aria-hidden="true">{n}</span>
  <h3>{esc(title)}</h3>
  <p>{esc(text)}</p>
</div>"""
        for n, title, text in STEPS[lang]
    )

    faq = "\n".join(
        f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
        for q, a in FAQ[lang]
    )

    base = SITE_URL if lang == "uk" else f"{SITE_URL}/it"
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": p["url"] if lang == "uk" else p["url_it"],
                "name": p["title"] if lang == "uk" else p["title_it"],
            }
            for i, p in enumerate(reversed(shown), 1)
        ],
    }
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME[lang],
        "url": base + "/",
        "inLanguage": lang,
        "description": CHANNEL_DESC if lang == "uk" else CHANNEL_DESC_IT,
    }

    other = ""
    if lang == "it":
        other = (
            f'<p class="sub">{t["only_translated"]} '
            f'<a href="{SITE_URL}/">Рим для своїх →</a></p>'
        )

    body = f"""
<div class="wrap">
  <section class="hero">
    <span class="badge">{t["badge"]}</span>
    <h1>{t["h1"]}</h1>
    <p class="lead">{t["lead"]}</p>
    <a class="cta" href="{CHANNEL_URL}" rel="noopener">{t["cta"]}</a>
    <a class="cta secondary" href="{base}/#posts">{t["cta2"]}</a>
    <div class="meta">
      <span>{t["meta"][0]}</span>
      <span>{t["meta"][1]}</span>
      <span>{t["meta"][2]}</span>
    </div>
  </section>
</div>

<section id="topics">
  <div class="wrap">
    <h2>{t["topics_h2"]}</h2>
    <p class="sub">{t["topics_sub"]}</p>
    <div class="grid topics">
{topics}
    </div>
  </div>
</section>

<section id="posts">
  <div class="wrap">
    <h2>{t["posts_h2"]}</h2>
    <p class="sub">{t["posts_sub"]}</p>
    <div class="grid posts">
{cards}
    </div>
    {other}
  </div>
</section>

<section>
  <div class="wrap">
    <h2>{t["how_h2"]}</h2>
    <p class="sub">{t["how_sub"]}</p>
    <div class="grid steps">
{steps}
    </div>
  </div>
</section>

<section id="faq">
  <div class="wrap">
    <h2>{t["faq_h2"]}</h2>
    <p class="sub">{t["faq_sub"]}</p>
    <div class="faq">
{faq}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="band">
      <div>
        <h2>{t["band_h2"]}</h2>
        <p>{t["band_p"]}</p>
      </div>
      <a class="cta" href="{CHANNEL_URL}" rel="noopener">{t["cta"]}</a>
    </div>
  </div>
</section>
"""
    extra = (
        f'<script type="application/ld+json">{json.dumps(website, ensure_ascii=False)}</script>\n'
        f'<script type="application/ld+json">{json.dumps(item_list, ensure_ascii=False)}</script>\n'
        f'<script type="application/ld+json">{org_schema()}</script>'
    )
    alts = [("uk", SITE_URL + "/"), ("it", f"{SITE_URL}/it/"), ("x-default", SITE_URL + "/")]
    switch = (f"{SITE_URL}/it/", "it") if lang == "uk" else (SITE_URL + "/", "uk")
    return page_shell(
        t["title_index"],
        t["desc_index"],
        base + "/",
        body,
        extra,
        lang=lang,
        alts=alts,
        switch=switch,
    )


def post_page(post: dict, prev: dict | None, nxt: dict | None, lang: str = "uk") -> str:
    import json

    t = TEXT[lang]
    it = lang == "it"
    title = post["title_it"] if it else post["title"]
    text = post["text_it"] if it else post["text"]
    url = post["url_it"] if it else post["url"]
    excerpt = post["excerpt_it"] if it else post["excerpt"]
    base = f"{SITE_URL}/it" if it else SITE_URL
    post_url = lambda p: p["url_it"] if it else p["url"]
    post_title = lambda p: p["title_it"] if it else p["title"]

    pager = []
    if prev:
        pager.append(f'<a href="{post_url(prev)}">← {esc(post_title(prev))}</a>')
    else:
        pager.append("<span></span>")
    if nxt:
        pager.append(f'<a href="{post_url(nxt)}">{esc(post_title(nxt))} →</a>')

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": excerpt,
        "datePublished": post["date"].strftime("%Y-%m-%d"),
        "dateModified": post["date"].strftime("%Y-%m-%d"),
        "inLanguage": lang,
        "image": f"{SITE_URL}/covers/{post['cover'].name}",
        "author": {"@type": "Organization", "name": BRAND[lang]},
        "publisher": {
            "@type": "Organization",
            "name": BRAND[lang],
            "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/avatar.png"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }

    alts = [("uk", post["url"])]
    if post["text_it"]:
        alts += [("it", post["url_it"]), ("x-default", post["url"])]
    switch = (post["url"], "uk") if it else ((post["url_it"], "it") if post["text_it"] else None)

    body = f"""
<div class="wrap post-page">
  <div class="crumbs"><a href="{base}/">{t["home"]}</a> · <a href="{base}/#posts">{t["posts_crumb"]}</a></div>
  <h1>{esc(title)}</h1>
  <time datetime="{post['date'].strftime('%Y-%m-%d')}">{human_date_lang(post['date'], lang)}</time>
  <div class="cover">
    <img src="{SITE_URL}/covers/{post['cover'].name}" alt="{esc(title)}" width="1080" height="810">
  </div>
  <div class="post-text">{paragraphs(text)}</div>
  <p style="margin-top:24px"><a class="cta" href="{CHANNEL_URL}" rel="noopener">{t["read_tg"]}</a></p>
  <nav class="pager">{"".join(pager)}</nav>
</div>
"""
    return page_shell(
        f"{title} — {BRAND[lang]}",
        excerpt,
        url,
        body,
        f'<script type="application/ld+json">{json.dumps(article, ensure_ascii=False)}</script>',
        image=f"{SITE_URL}/covers/{post['cover'].name}",
        lang=lang,
        alts=alts,
        switch=switch,
    )


def sitemap(posts: list[dict]) -> str:
    last = posts[-1]["date"] if posts else datetime.now(timezone.utc)
    it_posts = [p for p in posts if p["text_it"]]

    def row(url: str, date: datetime, changefreq: str, priority: str, alts: list[tuple[str, str]]) -> str:
        links = "".join(
            f'<xhtml:link rel="alternate" hreflang="{code}" href="{xml_escape(href)}"/>'
            for code, href in alts
        )
        return (
            f"  <url><loc>{xml_escape(url)}</loc>"
            f"<lastmod>{date.strftime('%Y-%m-%d')}</lastmod>"
            f"<changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority>{links}</url>"
        )

    rows = []
    home_alts = [("uk", SITE_URL + "/")] + ([("it", SITE_URL + "/it/")] if it_posts else [])
    rows.append(row(SITE_URL + "/", last, "weekly", "1.0", home_alts))
    if it_posts:
        rows.append(row(f"{SITE_URL}/it/", last, "weekly", "1.0", home_alts + [("x-default", SITE_URL + "/")]))
    for post in posts:
        rows.append(row(post["url"], post["date"], "monthly", "0.8", [("uk", post["url"])] + ([("it", post["url_it"])] if post["text_it"] else [])))
        if post["text_it"]:
            rows.append(row(post["url_it"], post["date"], "monthly", "0.8", [("uk", post["url"]), ("it", post["url_it"]), ("x-default", post["url"])]))
    body = "\n".join(rows)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        f"{body}\n</urlset>\n"
    )


def rss(posts: list[dict]) -> str:
    items = "\n".join(
        f"""    <item>
      <title>{xml_escape(p['title'])}</title>
      <link>{xml_escape(p['url'])}</link>
      <guid isPermaLink="true">{xml_escape(p['url'])}</guid>
      <pubDate>{p['date'].strftime('%a, %d %b %Y 09:00:00 +0100')}</pubDate>
      <description>{xml_escape(p['excerpt'])}</description>
    </item>"""
        for p in posts
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{xml_escape(CHANNEL_TITLE)}</title>
    <link>{xml_escape(SITE_URL)}/</link>
    <description>{xml_escape(CHANNEL_DESC)}</description>
    <language>uk</language>
    <atom:link href="{xml_escape(SITE_URL)}/rss.xml" rel="self" type="application/rss+xml"/>
{items}
  </channel>
</rss>
"""


def robots() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )


def not_found() -> str:
    body = f"""
<div class="wrap post-page">
  <h1>Сторінку не знайдено</h1>
  <p>Можливо, посилання застаріло. Перейдіть на <a href="{SITE_URL}/">головну</a> або відкрийте канал у Telegram.</p>
  <p style="margin-top:24px"><a class="cta" href="{CHANNEL_URL}" rel="noopener">Відкрити Telegram →</a></p>
</div>
"""
    return page_shell("404 — Рим для своїх", "Сторінку не знайдено.", SITE_URL + "/404.html", body)


def indexnow_key() -> str:
    if KEY_FILE.exists():
        value = KEY_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    import secrets

    value = secrets.token_hex(16)
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(value + "\n", encoding="utf-8")
    return value


def main() -> None:
    posts = load_posts()
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "posts").mkdir(parents=True)
    (DOCS / "it" / "posts").mkdir(parents=True)
    (DOCS / "covers").mkdir(parents=True)

    for cover in COVERS.glob("*.png"):
        shutil.copy2(cover, DOCS / "covers" / cover.name)

    avatar = ROOT / "brand/avatar.png"
    if avatar.exists():
        shutil.copy2(avatar, DOCS / "avatar.png")

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    # GitHub Pages: кастомний домен зберігається у docs/CNAME
    (DOCS / "CNAME").write_text(urlparse(SITE_URL).netloc + "\n", encoding="utf-8")
    (DOCS / "index.html").write_text(index_page(posts, "uk"), encoding="utf-8")
    (DOCS / "404.html").write_text(not_found(), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(sitemap(posts), encoding="utf-8")
    (DOCS / "robots.txt").write_text(robots(), encoding="utf-8")
    (DOCS / "rss.xml").write_text(rss(posts), encoding="utf-8")

    for i, post in enumerate(posts):
        prev = posts[i - 1] if i > 0 else None
        nxt = posts[i + 1] if i + 1 < len(posts) else None
        (DOCS / "posts" / f"{post['slug']}.html").write_text(
            post_page(post, prev, nxt, "uk"), encoding="utf-8"
        )

    it_posts = [post for post in posts if post["text_it"]]
    if it_posts:
        (DOCS / "it" / "index.html").write_text(index_page(posts, "it"), encoding="utf-8")
        for i, post in enumerate(it_posts):
            prev = it_posts[i - 1] if i > 0 else None
            nxt = it_posts[i + 1] if i + 1 < len(it_posts) else None
            (DOCS / "it" / "posts" / f"{post['slug']}.html").write_text(
                post_page(post, prev, nxt, "it"), encoding="utf-8"
            )

    key = indexnow_key()
    (DOCS / f"{key}.txt").write_text(key + "\n", encoding="utf-8")

    print(f"Сайт згенеровано → {DOCS}")
    print(f"  index.html · {len(posts)} постів · sitemap.xml · robots.txt · rss.xml")
    print(f"  it/: {len(it_posts)} перекладених постів")
    print(f"  IndexNow key: {key} → docs/{key}.txt")
    print(f"  SITE_URL: {SITE_URL}")


if __name__ == "__main__":
    main()

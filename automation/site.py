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

TOPICS = [
    ("🗓", "Події та виставки", "Куди піти цього тижня: безкоштовні події, виставки, що закриваються, ярмарки."),
    ("🚇", "Транспорт", "Страйки, ремонти, закриття станцій, зміни маршрутів Roma-Lido, метро й автобусів."),
    ("🏠", "Житло й робота", "Оренда без посередників, вакансії, курси італійської, легальне працевлаштування."),
    ("🏥", "Здоров'я", "Лікарі, аналізи, SSN, невідкладна допомога, де шукати україномовного лікаря."),
    ("⚠️", "Безпека", "Шахрайство, фішинг, райони, що робити в складній ситуації."),
    ("🇺🇦", "Україна і світ", "Коротко про головне — без паніки й без клікбейту."),
]

STEPS = [
    ("1", "Відкрийте канал", "Натисніть кнопку «Відкрити в Telegram» — канал публічний, читати можна без акаунта у вебверсії."),
    ("2", "Підпишіться", "Один дайджест на тиждень. Нічого зайвого: лише те, що стосується життя в Римі."),
    ("3", "Повертайтеся", "Якщо загубили пост — усі матеріали зібрані на цьому сайті."),
]

FAQ = [
    ("Це офіційний канал?", "Ні. Це незалежний дайджест для українців, які нещодавно переїхали до Риму. Ми не установа й не посередник."),
    ("Скільки коштує підписка?", "Нічого. Канал безкоштовний, без реклами й без платних підписок."),
    ("Звідки беруться новини?", "З відкритих джерел: ANSA, Corriere Roma, Il Messaggero, Il Tempo, AGI, Adnkronos, Il Sole 24 Ore, Il Fatto Quotidiano та офіційних сайтів."),
    ("Чи можна писати вам?", "Так, у коментарях під постами. Питання й пропозиції допомагають робити дайджест кориснішим."),
]

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


def load_posts() -> list[dict]:
    texts = code_blocks(CONTENT)
    covers = cover_files()
    if len(texts) != len(covers):
        raise SystemExit(
            f"Постів {len(texts)}, обкладинок {len(covers)} — кількість має збігатися."
        )
    posts = []
    for text, cover in zip(texts, covers):
        posts.append(make_post(text, cover))
    posts.extend(extra_posts())
    posts.sort(key=lambda post: (post["date"], post["slug"]))
    return posts


def make_post(text: str, cover: Path) -> dict:
    return {
        "text": text,
        "cover": cover,
        "slug": slug_from_cover(cover),
        "date": post_date(cover),
        "title": first_line(text),
        "excerpt": excerpt(text),
        "url": f"{SITE_URL}/posts/{slug_from_cover(cover)}.html",
    }


def extra_posts() -> list[dict]:
    """Окремі пости з content/extra/<slug>.md + covers/<slug>.png."""
    posts = []
    for path in sorted(EXTRA.glob("*.md")):
        cover = COVERS / f"{path.stem}.png"
        if not cover.exists():
            raise SystemExit(f"Немає обкладинки {cover.name} для content/extra/{path.name}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        posts.append(make_post(text, cover))
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


def page_shell(title: str, description: str, canonical: str, body: str, extra_head: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(CHANNEL_TITLE)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{SITE_URL}/covers/2026-11-09-intro.png">
<meta property="og:locale" content="uk_UA">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{SITE_URL}/covers/2026-11-09-intro.png">
<link rel="alternate" type="application/rss+xml" title="{esc(CHANNEL_TITLE)}" href="{SITE_URL}/rss.xml">
<link rel="icon" type="image/png" href="{SITE_URL}/avatar.png">
<style>{CSS}</style>
{extra_head}
</head>
<body>
<a class="skip" href="#main">Перейти до змісту</a>
<header class="site">
  <div class="wrap">
    <img src="{SITE_URL}/avatar.png" alt="Аватар каналу «Рим для своїх»" width="38" height="38">
    <span class="brand">Рим для своїх</span>
    <nav>
      <a href="{SITE_URL}/#topics">Теми</a>
      <a href="{SITE_URL}/#posts">Пости</a>
      <a href="{SITE_URL}/#faq">Питання</a>
      <a href="{CHANNEL_URL}" rel="noopener">Telegram</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site">
  <div class="wrap">
    <span>© 2026 «Рим для своїх». Незалежний дайджест для українців у Римі.</span>
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


def index_page(posts: list[dict]) -> str:
    import json

    cards = "\n".join(
        f"""<article class="post">
  <a href="{SITE_URL}/posts/{p['slug']}.html"><img src="{SITE_URL}/covers/{p['cover'].name}" alt="{esc(p['title'])}" loading="lazy" width="640" height="480"></a>
  <div class="body">
    <time datetime="{p['date'].strftime('%Y-%m-%d')}">{human_date(p['date'])}</time>
    <h3><a href="{SITE_URL}/posts/{p['slug']}.html">{esc(p['title'])}</a></h3>
    <p>{esc(p['excerpt'])}</p>
    <a class="more" href="{SITE_URL}/posts/{p['slug']}.html">Читати →</a>
  </div>
</article>"""
        for p in posts
    )

    topics = "\n".join(
        f"""<div class="card">
  <div class="icon" aria-hidden="true">{icon}</div>
  <h3>{esc(title)}</h3>
  <p>{esc(text)}</p>
</div>"""
        for icon, title, text in TOPICS
    )

    steps = "\n".join(
        f"""<div class="step">
  <span class="n" aria-hidden="true">{n}</span>
  <h3>{esc(title)}</h3>
  <p>{esc(text)}</p>
</div>"""
        for n, title, text in STEPS
    )

    faq = "\n".join(
        f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
        for q, a in FAQ
    )

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": p["url"],
                "name": p["title"],
            }
            for i, p in enumerate(posts, 1)
        ],
    }
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": CHANNEL_TITLE,
        "url": SITE_URL,
        "inLanguage": "uk",
        "description": CHANNEL_DESC,
    }

    body = f"""
<div class="wrap">
  <section class="hero">
    <span class="badge">🇺🇦🇮🇹 Телеграм-канал для українців у Римі</span>
    <h1>Рим для своїх — щотижневий дайджест для українців у Римі</h1>
    <p class="lead">Події, транспорт, житло, робота, здоров'я й безпека. Коротко, з джерелами, без паніки. Для тих, хто нещодавно переїхав до Риму або вже живе тут.</p>
    <a class="cta" href="{CHANNEL_URL}" rel="noopener">Відкрити в Telegram →</a>
    <a class="cta secondary" href="{SITE_URL}/#posts">Останні пости</a>
    <div class="meta">
      <span>📅 Один дайджест на тиждень</span>
      <span>🔗 Джерела в кожному пості</span>
      <span>🆓 Безкоштовно</span>
    </div>
  </section>
</div>

<section id="topics">
  <div class="wrap">
    <h2>Що всередині</h2>
    <p class="sub">Шість рубрик, які закривають перші місяці життя в Римі.</p>
    <div class="grid topics">
{topics}
    </div>
  </div>
</section>

<section id="posts">
  <div class="wrap">
    <h2>Останні пости</h2>
    <p class="sub">Ті самі матеріали, що виходять у каналі — зручно читати й пересилати.</p>
    <div class="grid posts">
{cards}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <h2>Як це працює</h2>
    <p class="sub">Три кроки — і ви нічого не пропустите.</p>
    <div class="grid steps">
{steps}
    </div>
  </div>
</section>

<section id="faq">
  <div class="wrap">
    <h2>Часті питання</h2>
    <p class="sub">Коротко про формат і правила.</p>
    <div class="faq">
{faq}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="band">
      <div>
        <h2>Приєднуйтеся до «Рим для своїх»</h2>
        <p>Щотижня — найважливіше для українців у Римі. Без паніки, з джерелами.</p>
      </div>
      <a class="cta" href="{CHANNEL_URL}" rel="noopener">Відкрити Telegram →</a>
    </div>
  </div>
</section>
"""
    extra = (
        f'<script type="application/ld+json">{json.dumps(website, ensure_ascii=False)}</script>\n'
        f'<script type="application/ld+json">{json.dumps(item_list, ensure_ascii=False)}</script>\n'
        f'<script type="application/ld+json">{org_schema()}</script>'
    )
    return page_shell(
        "Рим для своїх — телеграм-канал для українців у Римі",
        "Щотижневий дайджест для українців у Римі: події, транспорт, житло, робота, здоров'я, безпека. Без паніки, з джерелами.",
        SITE_URL + "/",
        body,
        extra,
    )


def post_page(post: dict, prev: dict | None, nxt: dict | None) -> str:
    import json

    pager = []
    if prev:
        pager.append(f'<a href="{SITE_URL}/posts/{prev["slug"]}.html">← {esc(prev["title"])}</a>')
    else:
        pager.append("<span></span>")
    if nxt:
        pager.append(f'<a href="{SITE_URL}/posts/{nxt["slug"]}.html">{esc(nxt["title"])} →</a>')

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": post["excerpt"],
        "datePublished": post["date"].strftime("%Y-%m-%d"),
        "dateModified": post["date"].strftime("%Y-%m-%d"),
        "inLanguage": "uk",
        "image": f"{SITE_URL}/covers/{post['cover'].name}",
        "author": {"@type": "Organization", "name": "Рим для своїх"},
        "publisher": {
            "@type": "Organization",
            "name": "Рим для своїх",
            "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/avatar.png"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": post["url"]},
    }

    body = f"""
<div class="wrap post-page">
  <div class="crumbs"><a href="{SITE_URL}/">Головна</a> · <a href="{SITE_URL}/#posts">Пости</a></div>
  <h1>{esc(post["title"])}</h1>
  <time datetime="{post['date'].strftime('%Y-%m-%d')}">{human_date(post['date'])}</time>
  <div class="cover">
    <img src="{SITE_URL}/covers/{post['cover'].name}" alt="{esc(post['title'])}" width="1080" height="810">
  </div>
  <div class="post-text">{paragraphs(post["text"])}</div>
  <p style="margin-top:24px"><a class="cta" href="{CHANNEL_URL}" rel="noopener">Читати в Telegram →</a></p>
  <nav class="pager">{"".join(pager)}</nav>
</div>
"""
    return page_shell(
        f"{post['title']} — Рим для своїх",
        post["excerpt"],
        post["url"],
        body,
        f'<script type="application/ld+json">{json.dumps(article, ensure_ascii=False)}</script>',
    )


def sitemap(posts: list[dict]) -> str:
    urls = [
        (SITE_URL + "/", posts[-1]["date"] if posts else datetime.now(timezone.utc)),
    ] + [(p["url"], p["date"]) for p in posts]
    rows = "\n".join(
        f"  <url><loc>{xml_escape(url)}</loc>"
        f"<lastmod>{date.strftime('%Y-%m-%d')}</lastmod>"
        f"<changefreq>{'weekly' if url.endswith('/') else 'monthly'}</changefreq>"
        f"<priority>{'1.0' if url.endswith('/') else '0.8'}</priority></url>"
        for url, date in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{rows}\n</urlset>\n"
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
    (DOCS / "covers").mkdir(parents=True)

    for cover in COVERS.glob("*.png"):
        shutil.copy2(cover, DOCS / "covers" / cover.name)

    avatar = ROOT / "brand/avatar.png"
    if avatar.exists():
        shutil.copy2(avatar, DOCS / "avatar.png")

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    # GitHub Pages: кастомний домен зберігається у docs/CNAME
    (DOCS / "CNAME").write_text(urlparse(SITE_URL).netloc + "\n", encoding="utf-8")
    (DOCS / "index.html").write_text(index_page(posts), encoding="utf-8")
    (DOCS / "404.html").write_text(not_found(), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(sitemap(posts), encoding="utf-8")
    (DOCS / "robots.txt").write_text(robots(), encoding="utf-8")
    (DOCS / "rss.xml").write_text(rss(posts), encoding="utf-8")

    for i, post in enumerate(posts):
        prev = posts[i - 1] if i > 0 else None
        nxt = posts[i + 1] if i + 1 < len(posts) else None
        (DOCS / "posts" / f"{post['slug']}.html").write_text(
            post_page(post, prev, nxt), encoding="utf-8"
        )

    key = indexnow_key()
    (DOCS / f"{key}.txt").write_text(key + "\n", encoding="utf-8")

    print(f"Сайт згенеровано → {DOCS}")
    print(f"  index.html · {len(posts)} постів · sitemap.xml · robots.txt · rss.xml")
    print(f"  IndexNow key: {key} → docs/{key}.txt")
    print(f"  SITE_URL: {SITE_URL}")


if __name__ == "__main__":
    main()

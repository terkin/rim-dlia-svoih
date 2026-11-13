#!/usr/bin/env python3
"""Генерує обкладинки 1080×810 для постів каналу «Рим для своїх»."""
from pathlib import Path
from html import escape

OUT = Path(__file__).parent

COVERS = [
    {
        "file": "2026-11-09-intro",
        "kicker": "ЗНАЙОМСТВО",
        "title": ["РИМ", "ДЛЯ СВОЇХ"],
        "sub": "Щотижневий дайджест для українців",
        "date": "СТАРТ 09.11.2026",
        "accent": "#FFD166",
        "icon": "home",
    },
    {
        "file": "2026-11-10-transport",
        "kicker": "ТРАНСПОРТ",
        "title": ["ЩО ЗМІНИЛОСЯ", "ЦЬОГО ТИЖНЯ"],
        "sub": "Roma-Lido · Lepanto · страйки 20–21.11",
        "date": "9–15 ЛИСТОПАДА",
        "accent": "#5FD3C4",
        "icon": "metro",
    },
    {
        "file": "2026-11-10-rent",
        "kicker": "ЖИТЛО Й ГРОШІ",
        "title": ["СКІЛЬКИ", "КОШТУЄ РИМ"],
        "sub": "Оренда · ярмарок · здоров'я · культура",
        "date": "10 ЛИСТОПАДА",
        "accent": "#FFB86B",
        "icon": "wallet",
    },
    {
        "file": "2026-11-10-events",
        "kicker": "КАЛЕНДАР",
        "title": ["РИМ ПЕРЕД", "СВЯТАМИ"],
        "sub": "Japan Days · екологічна неділя · ярмарки",
        "date": "14.11 — 08.12",
        "accent": "#E5C07B",
        "icon": "pin",
    },
    {
        "file": "2026-11-10-codice-fiscale",
        "kicker": "ДОКУМЕНТИ",
        "title": ["CODICE", "FISCALE"],
        "sub": "16 символів, без яких нічого не оформити",
        "date": "БЕЗКОШТОВНО",
        "accent": "#7FB2F0",
        "icon": "doc",
    },
    {
        "file": "2026-11-10-italy-military-aid",
        "kicker": "УКРАЇНА І СВІТ",
        "title": ["13-Й ПАКЕТ", "ДОПОМОГИ"],
        "sub": "Італія підтвердила нову військову підтримку",
        "date": "10 ЛИСТОПАДА",
        "accent": "#6EC1FF",
        "icon": "shield",
    },
    {
        "file": "2026-11-13-weekend-14-15",
        "kicker": "ВИХІДНІ",
        "title": ["ПЛАН НА", "14–15 ЛИСТОПАДА"],
        "sub": "Рим і околиці: Japan Days, 100 Cellos, borghi",
        "date": "14–15 ЛИСТОПАДА",
        "accent": "#A78BFA",
        "icon": "pin",
    },
    {
        "file": "2026-11-13-peace-talks-eu",
        "kicker": "УКРАЇНА І СВІТ",
        "title": ["ПЕРЕГОВОРИ", "І ДЕДЛАЙН ЄС"],
        "sub": "Kushner: «значний прогрес» · представник Європи — за 1–2 тижні",
        "date": "13 ЛИСТОПАДА",
        "accent": "#6EC1FF",
        "icon": "doc",
    },
    {
        "file": "2026-11-12-school-alerts",
        "kicker": "БЕЗПЕКА",
        "title": ["ШКОЛИ", "БЕЗ ПАНІКИ"],
        "sub": "Фальшиві загрози: заняття відбуваються · жовтий код",
        "date": "12 ЛИСТОПАДА",
        "accent": "#FF6B6B",
        "icon": "shield",
    },
    {
        "file": "2026-11-11-lazio-irpef",
        "kicker": "ПОДАТКИ",
        "title": ["МЕНШЕ", "ПОДАТКІВ"],
        "sub": "Лаціо: пільга для доходів до 35 000 €",
        "date": "З 1 СІЧНЯ 2027",
        "accent": "#7BD88F",
        "icon": "wallet",
    },
    {
        "file": "2026-11-11-rent-long-term",
        "kicker": "ЖИТЛО · ГАЙД",
        "title": ["КВАРТИРА", "ПОКРОКОВО"],
        "sub": "Довгострокова оренда в Римі: де шукати, як не обдурять",
        "date": "НОВИЙ ГАЙД",
        "accent": "#F4A261",
        "icon": "home",
    },
    {
        "file": "2026-11-11-kids",
        "kicker": "ВИХІДНІ З ДІТЬМИ",
        "title": ["КУДИ", "З ДІТЬМИ"],
        "sub": "4 події, які зайдуть дітям 4+",
        "date": "14–15 ЛИСТОПАДА",
        "accent": "#FF8A5B",
        "icon": "wheel",
    },
    {
        "file": "2026-11-12-exhibitions",
        "kicker": "КУЛЬТУРА",
        "title": ["ОСТАННІЙ", "ТИЖДЕНЬ"],
        "sub": "3 виставки закриваються 15 листопада",
        "date": "ДО 15 ЛИСТОПАДА",
        "accent": "#F2C14E",
        "icon": "frame",
    },
    {
        "file": "2026-11-13-money",
        "kicker": "ГРОШІ Й РОБОТА",
        "title": ["ОРЕНДА,", "РОБОТА, ЦІНИ"],
        "sub": "Job Day · дизель · ASL Roma 2",
        "date": "13 ЛИСТОПАДА",
        "accent": "#7BD88F",
        "icon": "wallet",
    },
    {
        "file": "2026-11-14-weekend",
        "kicker": "ПЛАН НА ВИХІДНІ",
        "title": ["КУДИ", "ПІТИ"],
        "sub": "Japan Days · ринки · Colletta Alimentare",
        "date": "14–15 ЛИСТОПАДА",
        "accent": "#8AB6FF",
        "icon": "pin",
    },
    {
        "file": "2026-11-15-digest",
        "kicker": "ТИЖНЕВИЙ ДАЙДЖЕСТ",
        "title": ["ГОЛОВНЕ", "ЗА ТИЖДЕНЬ"],
        "sub": "Транспорт · культура · діти · практичне",
        "date": "9–15 ЛИСТОПАДА",
        "accent": "#C9A7FF",
        "icon": "mail",
    },
]


def icon(kind: str, accent: str) -> str:
    cx, cy, r = 862, 545, 112
    base = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{accent}" stroke-opacity="0.45" stroke-width="2"/>'
    if kind == "wheel":
        spokes = []
        for angle in range(0, 360, 45):
            import math
            a = math.radians(angle)
            x = cx + 74 * math.cos(a)
            y = cy + 74 * math.sin(a)
            spokes.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{accent}" stroke-width="3" stroke-opacity="0.8"/>')
            spokes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{accent}"/>')
        return base + f'<circle cx="{cx}" cy="{cy}" r="76" fill="none" stroke="{accent}" stroke-width="4"/>' + "".join(spokes) + f'<circle cx="{cx}" cy="{cy}" r="10" fill="{accent}"/>'
    if kind == "frame":
        return base + (
            f'<rect x="{cx-72}" y="{cy-60}" width="144" height="120" rx="6" fill="none" stroke="{accent}" stroke-width="4"/>'
            f'<circle cx="{cx-34}" cy="{cy-24}" r="10" fill="{accent}"/>'
            f'<path d="M{cx-60} {cy+44} L{cx-14} {cy-4} L{cx+18} {cy+26} L{cx+46} {cy-10} L{cx+60} {cy+44} Z" fill="{accent}" opacity="0.85"/>'
        )
    if kind == "pin":
        return base + (
            f'<path d="M{cx} {cy-78} C{cx-46} {cy-78} {cx-62} {cy-34} {cx-62} {cy-8} C{cx-62} {cy+38} {cx} {cy+82} {cx} {cy+82} C{cx} {cy+82} {cx+62} {cy+38} {cx+62} {cy-8} C{cx+62} {cy-34} {cx+46} {cy-78} {cx} {cy-78} Z" fill="none" stroke="{accent}" stroke-width="4"/>'
            f'<circle cx="{cx}" cy="{cy-16}" r="22" fill="{accent}"/>'
        )
    if kind == "home":
        return base + (
            f'<path d="M{cx-70} {cy+10} L{cx} {cy-62} L{cx+70} {cy+10}" fill="none" stroke="{accent}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M{cx-52} {cy-2} L{cx-52} {cy+66} L{cx+52} {cy+66} L{cx+52} {cy-2}" fill="none" stroke="{accent}" stroke-width="5" stroke-linejoin="round"/>'
            f'<rect x="{cx-16}" y="{cy+22}" width="32" height="44" rx="4" fill="{accent}"/>'
        )
    if kind == "wallet":
        return base + (
            f'<rect x="{cx-70}" y="{cy-46}" width="140" height="92" rx="14" fill="none" stroke="{accent}" stroke-width="4"/>'
            f'<path d="M{cx-70} {cy-16} L{cx+70} {cy-16}" stroke="{accent}" stroke-width="3" stroke-opacity="0.5"/>'
            f'<rect x="{cx+22}" y="{cy-6}" width="48" height="32" rx="8" fill="{accent}"/>'
            f'<circle cx="{cx+46}" cy="{cy+10}" r="5" fill="#0A1424"/>'
        )
    if kind == "doc":
        return base + (
            f'<path d="M{cx-52} {cy-72} L{cx+24} {cy-72} L{cx+56} {cy-40} L{cx+56} {cy+72} L{cx-52} {cy+72} Z" fill="none" stroke="{accent}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="M{cx+24} {cy-72} L{cx+24} {cy-40} L{cx+56} {cy-40}" fill="none" stroke="{accent}" stroke-width="4" stroke-linejoin="round"/>'
            f'<line x1="{cx-28}" y1="{cy-16}" x2="{cx+32}" y2="{cy-16}" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>'
            f'<line x1="{cx-28}" y1="{cy+8}" x2="{cx+32}" y2="{cy+8}" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>'
            f'<line x1="{cx-28}" y1="{cy+32}" x2="{cx+12}" y2="{cy+32}" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>'
        )
    if kind == "shield":
        return base + (
            f'<path d="M{cx} {cy-78} L{cx+66} {cy-48} L{cx+66} {cy+4} C{cx+66} {cy+42} {cx+28} {cy+68} {cx} {cy+84} C{cx-28} {cy+68} {cx-66} {cy+42} {cx-66} {cy+4} L{cx-66} {cy-48} Z" fill="none" stroke="{accent}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="M{cx-24} {cy} L{cx-6} {cy+20} L{cx+28} {cy-18}" fill="none" stroke="{accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    if kind == "mail":
        return base + (
            f'<rect x="{cx-72}" y="{cy-50}" width="144" height="100" rx="12" fill="none" stroke="{accent}" stroke-width="4"/>'
            f'<path d="M{cx-64} {cy-40} L{cx} {cy+8} L{cx+64} {cy-40}" fill="none" stroke="{accent}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="M{cx-64} {cy+40} L{cx-18} {cy-2} M{cx+64} {cy+40} L{cx+18} {cy-2}" stroke="{accent}" stroke-width="3" stroke-opacity="0.6"/>'
        )
    # metro
    return base + (
        f'<rect x="{cx-64}" y="{cy-52}" width="128" height="104" rx="18" fill="none" stroke="{accent}" stroke-width="4"/>'
        f'<path d="M{cx-38} {cy+30} L{cx-38} {cy-24} L{cx} {cy+10} L{cx+38} {cy-24} L{cx+38} {cy+30}" fill="none" stroke="{accent}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<line x1="{cx-92}" y1="{cy+78}" x2="{cx+92}" y2="{cy+78}" stroke="{accent}" stroke-width="3" stroke-dasharray="10 10" stroke-opacity="0.7"/>'
    )


def colosseum(accent: str) -> str:
    # декоративні арки праворуч знизу
    parts = [f'<g opacity="0.10" fill="none" stroke="{accent}" stroke-width="4">']
    for i in range(6):
        x = 690 + i * 64
        parts.append(f'<path d="M{x} 790 L{x} 742 Q{x+22} 716 {x+44} 742 L{x+44} 790"/>')
    parts.append('</g>')
    return "".join(parts)


def cover(c: dict) -> str:
    accent = c["accent"]
    lines = c["title"]
    title_svg = []
    y = 330 if len(lines) == 2 else 360
    for line in lines:
        title_svg.append(
            f'<text x="80" y="{y}" font-family="PT Sans, Arial, sans-serif" '
            f'font-size="112" font-weight="800" fill="#FFFFFF" letter-spacing="-3">{escape(line)}</text>'
        )
        y += 122
    sub_y = y + 8
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="810" viewBox="0 0 1080 810">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0A1424"/>
      <stop offset="0.55" stop-color="#132844"/>
      <stop offset="1" stop-color="#1B3352"/>
    </linearGradient>
    <radialGradient id="glow" cx="82%" cy="18%" r="55%">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.30"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1080" height="810" fill="url(#bg)"/>
  <rect width="1080" height="810" fill="url(#glow)"/>
  <rect x="30" y="30" width="1020" height="750" rx="28" fill="none" stroke="{accent}" stroke-opacity="0.28" stroke-width="2"/>

  <g font-family="PT Sans, Arial, sans-serif">
    <circle cx="86" cy="92" r="9" fill="{accent}"/>
    <text x="110" y="100" font-size="22" font-weight="700" fill="#DCE8F4" letter-spacing="5">РИМ ДЛЯ СВОЇХ</text>
    <text x="994" y="100" text-anchor="end" font-size="20" font-weight="600" fill="#7F95A9" letter-spacing="3">РИМ · ІТАЛІЯ</text>

    <text x="80" y="230" font-size="24" font-weight="700" fill="{accent}" letter-spacing="5">{escape(c["kicker"])}</text>
    {"".join(title_svg)}
    <text x="82" y="{sub_y}" font-size="31" font-weight="500" fill="#C9D6E2">{escape(c["sub"])}</text>

    <rect x="80" y="638" width="{int(len(c["date"]) * 17 + 64)}" height="66" rx="33" fill="{accent}"/>
    <text x="112" y="682" font-size="27" font-weight="800" fill="#0A1424" letter-spacing="1">{escape(c["date"])}</text>

    <text x="80" y="752" font-size="18" font-weight="600" fill="#7F95A9" letter-spacing="3">t.me/rim_dlia_svoih</text>
  </g>

  {colosseum(accent)}
  {icon(c["icon"], accent)}
</svg>
'''


def main() -> None:
    for c in COVERS:
        path = OUT / f'{c["file"]}.svg'
        path.write_text(cover(c), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()

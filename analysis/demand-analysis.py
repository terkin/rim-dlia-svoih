#!/usr/bin/env python3
"""
Аналіз попиту для каналу «Рим для своїх»
Збирає дані про:
1. Конкурентів у Telegram
2. Пошукові запити (обсяг)
3. Активні Facebook-групи
4. Результати опитувань

Результат: reports/demand-analysis.json + зрозумілий звіт
"""

import json
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 1. Конкуренти в Telegram (через каталоги / пошук)
# ============================================================
TELEGRAM_SEED_KEYWORDS = [
    "українці Рим",
    "ukrainians Rome",
    "Рим українці",
    "ukrainians Italy",
    "українці Італія",
]

def analyze_telegram_competitors():
    """
    Збирає список каналів-конкурентів.
    Через Telegram API неможливо отримати повний список — 
    використовуємо каталоги (TGStat, Telemetr) та пошук.
    
    ЗАМІСТЬ прямого API: повертаємо структуру для ручного заповнення
    або інтеграцію з каталогами, якщо з'явиться доступ.
    """
    competitors = []
    
    # Приклад конкурентів (заповнити вручну або через API каталогів):
    # {
    #   "name": "Назва каналу",
    #   "username": "@username",
    #   "subscribers": 1500,
    #   "language": "uk/ru/en",
    #   "topic": "news/travel/info",
    #   "country": "IT",
    #   "last_post": "2026-11-08",
    #   "avg_views": 300,
    #   "note": "Прямий конкурент - дайджест подій"
    # }
    
    return {
        "analyzed_at": datetime.now().isoformat(),
        "keywords_searched": TELEGRAM_SEED_KEYWORDS,
        "competitors": competitors,
        "method": "Manual fill or integrate with directory APIs (TGStat, Telemetr)",
        "recommendation": "Add 5-10 competitors manually from tgstat.com catalog search"
    }

# ============================================================
# 2. Пошукові запити (Google Keyword Planner альтернативи)
# ============================================================
KEYWORD_SEEDS_UA = [
    "українці в Римі",
    "українці Рим телеграм",
    "Рим довідник укр",
    "codice fiscale Roma українською",
    "tessera sanitaria Рим українці",
    "робота в Римі укр",
    "оренда житла Рим українці",
    "події Рим вихідні укр",
    "українці Італія",
    "ukrainians in Rome telegram",
    "ukrainians in Italy",
    "ukrainian community Rome",
]

KEYWORD_SEEDS_IT = [
    "ucraini a Roma telegram",
    "ukraini Roma eventi",
    "comunità ucraina Roma",
]

def analyze_keywords(seed_list, language="uk"):
    """
    Перевірка обсягу запитів через:
    - Google Keyword Planner (потребує Google Ads акаунт)
    - Ahrefs Keyword Generator (безкоштовно, без реєстрації)
    - Ubersuggest (безкоштовна версія)
    - Google Trends (безкоштовно)
    
    ЗАМІСТЬ прямого API (недоступні без ключів):
    Повертаємо структуру для ручного заповнення або інтеграції.
    """
    results = []
    for keyword in seed_list:
        results.append({
            "keyword": keyword,
            "language": language,
            "search_volume": None,  # Заповнити вручну через https://ahrefs.com/keyword-generator
            "competition": None,
            "cpc": None,
            "trend": None,
            "source": None,
            "note": "Потрібно перевірити вручну на https://ahrefs.com/keyword-generator"
        })
    return results

def get_keyword_research_summary():
    """Зведення по всіх ключових словах."""
    ua = analyze_keywords(KEYWORD_SEEDS_UA, "uk")
    it = analyze_keywords(KEYWORD_SEEDS_IT, "it")
    
    return {
        "analyzed_at": datetime.now().isoformat(),
        "ukrainian_keywords": ua,
        "italian_keywords": it,
        "how_to_fill": (
            "Відкрийте https://ahrefs.com/keyword-generator, введіть кожне слово "
            "(або пакетно до 10) і скопіюйте 'Search volume' у поле search_volume"
        ),
        "expected_insights": [
            "Якщо 'українці в Римі' має >100 запитів/міс - попит є",
            "Якщо 'codice fiscale Roma укр' має >50 запитів/міс - потрібні практичні гайди",
            "Тренди показують, чи зростає інтерес (переезд після 2022)"
        ]
    }

# ============================================================
# 3. Facebook-групи (аналіз активності)
# ============================================================
FRIENDLY_GROUP_SEARCH_TERMS = [
    "Українці в Римі",
    "Українці в Італії",
    "Українці в Італії Рим",
    "Робота в Італії Рим",
    "Оренда житла Рим українці",
    "Українці в Лаціо",
    "Українці Esquilino",
    "Ukrainians in Rome",
    "Ukrainians in Italy",
]

def analyze_facebook_groups():
    """
    Пошук та аналіз Facebook-груп:
    - назва
    - кількість учасників
    - активність (постів/тиждень)
    - посилання
    
    ЗАМІСТЬ автоматичного парсингу (FB блокує):
    Повертаємо структуру для ручного заповнення.
    """
    groups = []
    for term in FRIENDLY_GROUP_SEARCH_TERMS:
        groups.append({
            "search_term": term,
            "found": False,
            "name": None,
            "url": None,
            "members": None,
            "posts_per_week": None,
            "activity_level": None,  # "high/medium/low"
            "note": "Виконати пошук вручну в Facebook"
        })
    return {
        "analyzed_at": datetime.now().isoformat(),
        "groups": groups,
        "method": "Manual search in Facebook"
    }

# ============================================================
# 4. Опитування аудиторії (збір відповідей)
# ============================================================
def analyze_survey_responses():
    """
    Збір та аналіз відповідей з опитування у FB-групах.
    
    Формат відповіді:
    {
        "question": "Чого вам найбільше бракує в інтернеті українською про Рим?",
        "responses": [
            {"group": "Українці в Римі", "answer": "транспорт"},
            ...
        ],
        "results": {
            "транспорт": 5,
            "житло": 3,
            ...
        }
    }
    """
    return {
        "analyzed_at": datetime.now().isoformat(),
        "survey_published": False,
        "responses_collected": 0,
        "results": {},
        "status": "Опитування ще не опубліковане"
    }

# ============================================================
# Головна функція - зведення звіту
# ============================================================
def generate_demand_analysis():
    """Збирає всі дані в один звіт."""
    
    telegram = analyze_telegram_competitors()
    keywords = get_keyword_research_summary()
    groups = analyze_facebook_groups()
    survey = analyze_survey_responses()
    
    report = {
        "project": "Рим для своїх (@rim_dlia_svoih)",
        "analysis_type": "demand_analysis",
        "generated_at": datetime.now().isoformat(),
        "telegram_competitors": telegram,
        "keyword_research": keywords,
        "facebook_groups": groups,
        "survey": survey,
        "conclusion": {
            "status": "needs_manual_verification",
            "next_steps": [
                "1. Перевірити ключові запити на https://ahrefs.com/keyword-generator",
                "2. Знайти 5-10 конкурентів через tgstat.com",
                "3. Опублікувати опитування в 3-5 FB-групах",
                "4. Заповнити дані в цьому звіті",
                "5. Оцінити попит: якщо >10 відповідей + ключові запити >100/міс - попит є"
            ]
        }
    }
    
    return report

if __name__ == "__main__":
    report = generate_demand_analysis()
    
    filename = OUTPUT_DIR / f"demand-analysis-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Звіт збережено: {filename}")
    print("\nЩоб отримати повні дані:")
    print("  1. Ключові запити: відкрийте Ahrefs Keyword Generator для кожного запиту")
    print("  2. Конкуренти: знайдіть через tgstat.com catalog")
    print("  3. Опитування: опублікуйте в FB-групах, зберіть відповіді")
    print("  4. Заповніть поля в цьому файлі вручну")

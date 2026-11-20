#!/bin/zsh
# Автопостинг для каналу @rim_dlia_svoih.
# Запускається launchd: 09:00 (morning) і 19:00 (evening).
# Ручний запуск:  automation/scheduled_post.sh morning
# Тест без публікації: automation/scheduled_post.sh test
set -u

REPO="/Users/terkin/rim-dlia-svoikh"
SLOT="${1:-morning}"
export PATH="/Users/terkin/.opencode/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
mkdir -p "$REPO/automation/logs"
cd "$REPO" || exit 1

STAMP=$(date +%Y-%m-%d-%H%M)
LOG="$REPO/automation/logs/$STAMP-$SLOT.log"

COMMON="Ти працюєш у репозиторії $REPO (сайт ucrainiroma.it + Telegram-канал @rim_dlia_svoih).
Спочатку прочитай README.md і дотримуйся описаного процесу. Уся текстова продукція — українською (сайт також має італійську версію в content/it/).
Ніколи не друкуй вміст .env і токени."

FOCUS="ГОЛОВНЕ ПРАВИЛО ФОКУСУ: пишемо ТІЛЬКИ про Рим і те, що безпосередньо стосується життя в Римі.
ЗАБОРОНЕНО як головну тему: світові новини (саміти, Трамп, Путін, Сі, війна, НАТО, Брюссель, Вашингтон), загальноукраїнські та загальноіталійські новини, якщо вони не мають прямої практичної дії на людину, яка живе в Римі.
Політика — лише місцева: рішення Comune di Roma / Regione Lazio, які змінюють правила життя в місті (транспорт, тарифи, дозволи, черги, послуги, ZTL, будівництво, парки).
Добре підходять: події та виставки в Римі, безкоштовні можливості, нові відкриття, ринки, страйки й транспорт, ціни/тарифи в Римі, дедлайни для резидентів, міські послуги, погода/екологічні неділі, поради для новачків.
Якщо новина світова, але має прямий римський кут (напр. зміна цін на пальне в Римі, закриття вулиці через саміт) — подавай САМЕ римський кут, а не саму світову подію."

MORNING="$COMMON
$FOCUS
Завдання: РАНКОВИЙ ВИПУСК. Зроби рівно ОДИН новий пост за сьогодні — про Рим.
1) Запусти python3 automation/collect.py і переглянь automation/candidates.json (джерела Il Messaggero Roma, Corriere Roma, RomaToday тощо).
2) Додатково пошукай у Google News RSS запити на кшталт: «Roma oggi», «Roma eventi <дата>», «Roma trasporti sciopero», «Roma gratis», «Roma apertura mostra». Факти підтверджуй 2+ джерелами або офіційним сайтом.
3) Обери 3–5 римських тем дня (подія/виставка, безкоштовна можливість, транспорт або страйк, практична дрібниця для новачка) і подай короткими блоками.
4) Не повторюй теми з content/extra/ за останні 2 дні.
5) Створи content/extra/<YYYY-MM-DD-slug>.md (повний текст), content/it/<slug>.md (італійський переклад того ж матеріалу), content/channel/<slug>-post.md (≤1024 символи, перевір len()).
6) Додай запис обкладинки у covers/generate.py (kicker/title/sub/date/accent/icon з наявних), згенеруй PNG через python3 covers/generate.py та /opt/homebrew/bin/rsvg-convert -w 1080 -h 810.
7) Запусти python3 automation/site.py, потім git add -A && git commit && git push origin main.
8) Опублікуй: python3 publish.py file content/channel/<slug>-post.md --cover covers/<slug>.png
9) Дочекайся білда GitHub Pages (gh api repos/terkin/rim-dlia-svoih/pages/builds) і запусти python3 automation/indexnow.py.
10) Перевір пост через https://t.me/s/rim_dlia_svoih і живі URL сайту.
Якщо римських новин мало — зроби корисний evergreen-пост для новачків у Римі (без повторів). Світові новини не публікуй навіть як запасний варіант."

EVENING="$COMMON
$FOCUS
Завдання: ВЕЧІРНІЙ ВИПУСК. Зроби рівно ОДИН новий пост — про Рим на завтра й вихідні.
1) Запусти python3 automation/collect.py і переглянь candidates.json + свіжі Google News RSS за сьогодні (запити «Roma eventi domani», «Roma weekend», «Roma sciopero trasporti»).
2) Обери 3–5 римських подій/новин на завтра й вихідні: виставки, безкоштовні події, концерти, ринки, транспорт і страйки, тимчасові закриття, дедлайни.
3) Не повторюй ранковий пост цього дня: перевір файли content/extra/ за сьогодні.
4) Створи content/extra/<YYYY-MM-DD-slug>.md, content/it/<slug>.md, content/channel/<slug>-post.md (≤1024 символи, перевір len()).
5) Обкладинка у covers/generate.py → python3 covers/generate.py → rsvg-convert -w 1080 -h 810.
6) python3 automation/site.py → git add -A && git commit && git push origin main.
7) python3 publish.py file content/channel/<slug>-post.md --cover covers/<slug>.png
8) Дочекайся білда Pages, python3 automation/indexnow.py, перевір t.me/s/rim_dlia_svoih і живі URL.
Якщо римських подій мало — зроби практичний римський пост (чекліст новачка, поради щодо транспорту/лікаря/житла) без повторів. Світові новини не публікуй."

TEST="$COMMON
Це тестовий запуск. Нічого не створюй, не змінюй, не публікуй. Просто перевір, що ти бачиш репозиторій: виконай head -5 automation/candidates.json. Відповідай одним словом OK."

case "$SLOT" in
  morning) TASK="$MORNING" ;;
  evening) TASK="$EVENING" ;;
  test)    TASK="$TEST" ;;
  *) echo "Usage: $0 [morning|evening|test]"; exit 2 ;;
esac

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') slot=$SLOT ==="
  /Users/terkin/.opencode/bin/opencode run --auto --model opencode/deepseek-v4.1-flash-free --title "Автопост $SLOT $STAMP" "$TASK"
  echo "exit=$?"
} >>"$LOG" 2>&1

# Залишаємо тільки 30 останніх логів
ls -1t "$REPO/automation/logs"/*.log 2>/dev/null | tail -n +31 | xargs -I{} rm -f {} 2>/dev/null

exit 0

# Digital Lab Office

ИИ-команда агентства Digital Lab. Работает через Claude Code на Mac по подписке Claude,
общение — в Telegram, задачи — в Supabase, дашборд — на Vercel.

| Сотрудник | Роль | Где живёт |
|---|---|---|
| Алиса | Ассистент, операционный директор | `CLAUDE.md` + Telegram |
| Дмитрий | Проджект-менеджер | `.claude/agents/dmitry.md` |
| Мария | Дизайнер | `.claude/agents/maria.md` |
| Максим | Веб-разработчик | `.claude/agents/maxim.md` |
| Илья | Боты и автоматизации | `.claude/agents/ilya.md` |
| Александр | Тестировщик | `.claude/agents/alexander.md` |
| Дарья | Маркетолог, привлечение клиентов | `.claude/agents/daria.md` |

## Структура
- `CLAUDE.md` — характер и правила Алисы
- `.claude/agents/` — коллеги Алисы
- `tools/tasks.ts` — работа с задачами и проектами
- `supabase/schema.sql` — база задач
- `dashboard/` — дашборд (Vercel, Root Directory = `dashboard`)
- `start-office.command` — запуск офиса двойным кликом

## Установка на Mac (один раз)
1. Bun: `curl -fsSL https://bun.sh/install | bash`
2. Claude Code: `curl -fsSL https://claude.ai/install.sh | bash`, затем `claude` и вход по подписке.
3. Склонировать репозиторий, в папке создать `.env` по образцу `.env.example`.
4. Supabase → SQL Editor → выполнить `supabase/schema.sql`.
5. В Claude Code: `/plugin install telegram@claude-plugins-official`, затем `/telegram:configure <токен бота Алисы>`.
6. Запустить `start-office.command`, написать боту, выполнить `/telegram:access pair <код>` и `/telegram:access policy allowlist`.

## Дашборд (Vercel)
Import репозитория → Root Directory `dashboard` → переменные:
`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `DASHBOARD_KEY` (любой длинный пароль),
`ALICE_BOT_TOKEN`, `OWNER_TELEGRAM_ID` (для входа из Telegram).
Открывать: `https://<проект>.vercel.app/?key=<DASHBOARD_KEY>` или кнопкой меню бота
(BotFather → Bot Settings → Menu Button → ссылка на дашборд).

# Digital Lab Office

ИИ-команда агентства Digital Lab в Telegram + дашборд задач.

| Сотрудник | Роль | Этап |
|---|---|---|
| Алиса | Ассистент, операционный директор | 1 ✅ |
| Дмитрий | Проджект-менеджер | 2 |
| Максим | Веб-разработчик (GitHub → Vercel) | 2 |
| Мария | Дизайнер | 3 |
| Илья | Боты и автоматизации | 3 |
| Александр | Тестировщик | 3 |
| Дарья | Маркетолог: продвижение и лиды | 3 |

## Структура
- `office/` — Алиса (Telegram-бот + Claude + инструменты задач)
- `supabase/schema.sql` — база проектов и задач
- `dashboard/` — дашборд (Vercel, открывается кнопкой из Telegram)
- `deploy/` — запуск на сервере

## Запуск
1. Supabase → SQL Editor → вставить `supabase/schema.sql` → Run.
2. Заполнить `.env` по образцу `.env.example`.
3. Сервер: склонировать в `/opt/digital-lab-office`, положить `.env`, `bash deploy/install.sh`.
4. Vercel: импортировать репозиторий, Root Directory = `dashboard`, переменные:
   `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ALICE_BOT_TOKEN`, `OWNER_TELEGRAM_ID`, `DASHBOARD_KEY`.
5. Ссылку Vercel вписать в `DASHBOARD_URL` и перезапустить: `systemctl restart digital-lab-office`.

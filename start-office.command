#!/bin/bash
# Digital Lab Office — запуск Алисы. Двойной клик по файлу, окно Терминала не закрывать.
cd "$(dirname "$0")"
git pull --quiet 2>/dev/null
caffeinate -ims -w $$ &          # Mac не уснёт, пока офис работает
claude "Начни рабочий день" --model sonnet --channels plugin:telegram@claude-plugins-official

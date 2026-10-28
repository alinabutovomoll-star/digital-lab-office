#!/bin/bash
# Digital Lab Office — запуск Алисы. Двойной клик по файлу, окно Терминала не закрывать.
cd "$(dirname "$0")"
git pull --quiet 2>/dev/null
caffeinate -ims -w $$ &          # Mac не уснёт, пока офис работает
claude --channels plugin:telegram@claude-plugins-official "Начни рабочий день"

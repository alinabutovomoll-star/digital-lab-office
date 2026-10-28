#!/usr/bin/env bash
# Установка на сервер (Ubuntu 22/24). Запуск: bash deploy/install.sh
set -e
apt-get update -y && apt-get install -y python3-venv git
cd /opt/digital-lab-office
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp deploy/digital-lab-office.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now digital-lab-office
systemctl status digital-lab-office --no-pager

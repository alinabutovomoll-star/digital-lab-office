#!/bin/bash
# Расшифровка голосового сообщения в текст — бесплатно, прямо на Mac (whisper.cpp).
#   bash tools/voice.sh /путь/к/voice.oga
# Один раз нужно установить: bash tools/voice.sh --install
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"   # Homebrew, даже если Терминал открыт до его установки
MODEL="$HOME/.whisper/ggml-small.bin"

if [ "$1" = "--install" ]; then
  if ! command -v brew >/dev/null; then
    echo "Сначала установи Homebrew: https://brew.sh"; exit 1
  fi
  brew install whisper-cpp ffmpeg
  mkdir -p "$HOME/.whisper"
  [ -f "$MODEL" ] || curl -L -o "$MODEL" \
    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
  echo "Готово: голосовые будут расшифровываться."
  exit 0
fi

IN="$1"
[ -f "$IN" ] || { echo "Нет файла: $IN"; exit 1; }
[ -f "$MODEL" ] || { echo "Модель не установлена. Запусти: bash tools/voice.sh --install"; exit 1; }
BIN=$(command -v whisper-cli || command -v whisper-cpp || true)
[ -n "$BIN" ] || { echo "whisper.cpp не установлен. Запусти: bash tools/voice.sh --install"; exit 1; }

WAV=$(mktemp -t voice).wav
ffmpeg -loglevel error -y -i "$IN" -ar 16000 -ac 1 "$WAV"
"$BIN" -m "$MODEL" -l ru -nt -np -f "$WAV" 2>/dev/null | sed '/^\s*$/d'
rm -f "$WAV"

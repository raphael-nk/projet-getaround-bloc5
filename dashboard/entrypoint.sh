#!/bin/sh
set -e

if [ -f /app/.env ]; then
  set -a
  . /app/.env
  set +a
fi

exec streamlit run main.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-7860}" \
  --server.headless=true

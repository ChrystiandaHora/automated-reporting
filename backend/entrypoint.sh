#!/bin/sh
set -e

# Se executando como root, garante a propriedade do volume montado /data para appuser
if [ "$(id -u)" = "0" ]; then
    if [ -d /data ]; then
        chown -R appuser:appuser /data 2>/dev/null || true
        chmod -R u+rwX /data 2>/dev/null || true
    fi
    exec runuser -u appuser -- "$@"
fi

exec "$@"


#!/bin/sh
set -e

# Garante inicialização e permissões no volume montado em /data
if [ "$(id -u)" = '0' ]; then
    mkdir -p /data
    chown -R nxguard:nxguard /data
    chmod 775 /data
    exec runuser -u nxguard -- "$@"
else
    exec "$@"
fi

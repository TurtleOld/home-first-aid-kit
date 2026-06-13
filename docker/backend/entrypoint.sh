#!/bin/sh
set -eu

sync_directory() {
    source_dir="$1"
    target_dir="$2"

    mkdir -p "$target_dir"
    find "$target_dir" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    cp -a "$source_dir"/. "$target_dir"/
}

chown -R app:app /app/backend/media /app/backend/staticfiles

if [ -d /app/runtime/frontend ]; then
    sync_directory /app/frontend/dist /app/runtime/frontend
fi

if [ -d /app/runtime/nginx ]; then
    mkdir -p /app/runtime/nginx
    cp /app/nginx/default.conf /app/runtime/nginx/default.conf
fi

export HOME=/app
exec setpriv --reuid=app --regid=app --clear-groups "$@"

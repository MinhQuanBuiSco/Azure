#!/bin/sh
set -e

# Default backend URL if not set
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Substitute environment variables in nginx config
sed -i "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf

echo "Starting nginx with backend URL: ${BACKEND_URL}"

# Execute nginx
exec nginx -g 'daemon off;'

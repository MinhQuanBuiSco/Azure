#!/bin/sh
set -e

# Replace environment variables in nginx config
# This allows dynamic backend URL configuration at runtime

# Default values
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"

# Create nginx config from template
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Execute CMD
exec "$@"

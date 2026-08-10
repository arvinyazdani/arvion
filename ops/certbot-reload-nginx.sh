#!/usr/bin/env bash
set -Eeuo pipefail

install -d -m 700 /etc/nginx/ssl
ln -sfn /etc/letsencrypt/live/rvionai.com/fullchain.pem /etc/nginx/ssl/rvionai.crt
ln -sfn /etc/letsencrypt/live/rvionai.com/privkey.pem /etc/nginx/ssl/rvionai.key
nginx -t
systemctl reload nginx

#!/usr/bin/env bash
# Đặt lại mật khẩu admin của 1 tenant. Dùng: reset.sh <tenant_id> <email>  (mật khẩu mới qua env TENANT_PASSWORD)
# Exit: 0 = OK · 1 = id sai · 3 = workspace không tồn tại · 4 = không tìm thấy tài khoản / lỗi.
set -euo pipefail

ID="${1:?Thiếu tenant_id}"; EMAIL="${2:?Thiếu email}"
DC="docker compose -f docker-compose.vps.yml"
PGUSER='${POSTGRES_USER:-odoo}'   # giải trong container

if ! printf '%s' "$ID" | grep -Eq '^[a-z0-9][a-z0-9-]{2,30}$'; then
  echo "✗ tenant_id không hợp lệ: $ID" >&2; exit 1
fi

# DB tenant tồn tại?
if ! $DC exec -T db bash -lc "psql -U $PGUSER -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$ID'\" | grep -q 1"; then
  echo "✗ Workspace '$ID' không tồn tại" >&2; exit 3
fi

# Đổi mật khẩu (odoo shell tìm user theo login = email; ORM → an toàn injection)
OUT=$($DC exec -T \
  -e TENANT_DB="$ID" -e TENANT_EMAIL="$EMAIL" -e TENANT_PASSWORD="${TENANT_PASSWORD:-}" \
  odoo bash -lc 'odoo shell -d "$TENANT_DB" --db_host="$HOST" --db_user="$USER" --db_password="$PASSWORD" --no-http' \
  < demo-data/packs/reset_password.py 2>/dev/null || true)

if ! printf '%s' "$OUT" | grep -q RESET_OK; then
  echo "✗ Không đặt lại được (email không khớp tài khoản workspace?)" >&2; exit 4
fi
echo "✅ Đã đặt lại mật khẩu cho $EMAIL @ $ID"

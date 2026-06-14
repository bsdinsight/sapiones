#!/usr/bin/env bash
# Provision 1 tenant Sapiones từ DB TEMPLATE `sapiones_tpl`. Login = email.
#   ./provision.sh <tenant_id> <email> "<tên công ty>" ["người liên hệ"] ["tỉnh"] ["sđt"]
# Ví dụ:
#   ./provision.sh 412345 hr@congtyabc.vn "Công ty May ABC" "Chị Lan" "Bình Dương" 0905123456
# Mật khẩu chủ: truyền qua env TENANT_PASSWORD (tuỳ chọn).
# License gói trả phí: truyền qua env TENANT_LICENSE (tuỳ chọn; trống = bản free).
# → tạo DB <tenant_id> (clone sapiones_tpl) + đặt công ty/chủ/license.
# Exit code 2 = id (DB) đã tồn tại → caller thử id khác.
set -euo pipefail

ID="${1:?Thiếu tenant_id}"
EMAIL="${2:?Thiếu email}"
COMPANY="${3:?Thiếu tên công ty}"
CONTACT="${4:-}"
PROV="${5:-}"
PHONE="${6:-}"

TPL="sapiones_tpl"
DC="docker compose -f docker-compose.vps.yml"
PGUSER='${POSTGRES_USER:-odoo}'   # giải trong container

# id chỉ cho phép [a-z0-9-], 3–31 ký tự (an toàn cho DB name + subdomain)
if ! printf '%s' "$ID" | grep -Eq '^[a-z0-9][a-z0-9-]{2,30}$'; then
  echo "✗ tenant_id không hợp lệ (chỉ a-z 0-9 -, 3–31 ký tự): $ID" >&2; exit 1
fi

echo "==> [1/2] Clone $TPL → $ID"
$DC exec -T db bash -lc "
  set -e
  U=$PGUSER
  if psql -U \"\$U\" -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$ID'\" | grep -q 1; then
    echo '✗ DB $ID đã tồn tại — chọn id khác' >&2; exit 2
  fi
  psql -U \"\$U\" -d postgres -tc \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$TPL' AND pid<>pg_backend_pid();\" >/dev/null 2>&1 || true
  createdb -U \"\$U\" -T \"$TPL\" \"$ID\"
"

echo "==> [2/2] Hậu xử lý tenant $ID (công ty/chủ/license)"
$DC exec -T \
  -e TENANT_DB="$ID" -e TENANT_EMAIL="$EMAIL" -e TENANT_COMPANY="$COMPANY" \
  -e TENANT_NAME="$CONTACT" -e TENANT_PROVINCE="$PROV" -e TENANT_PHONE="$PHONE" \
  -e TENANT_PASSWORD="${TENANT_PASSWORD:-}" -e TENANT_LICENSE="${TENANT_LICENSE:-}" \
  odoo bash -lc 'odoo shell -d "$TENANT_DB" --db_host="$HOST" --db_user="$USER" --db_password="$PASSWORD" --no-http' \
  < demo-data/packs/provision_setup.py

echo ""
echo "✅ XONG → https://$ID.sapiones.com   (đăng nhập email: $EMAIL)"
echo "   (DB tự phục vụ qua dbfilter=^%d\$ + tunnel ingress *.sapiones.com — không cần restart Odoo.)"

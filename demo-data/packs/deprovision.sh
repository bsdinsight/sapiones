#!/usr/bin/env bash
# Xoá HẲN 1 tenant: DB + filestore + bản ghi CF DNS. Dùng: deprovision.sh <tenant_id>
# CHẠY TỪ /root/sapiones. Exit: 0 OK · 1 id sai / DB được bảo vệ.
set -euo pipefail

ID="${1:?Thiếu tenant_id}"
DC="docker compose -f docker-compose.vps.yml"

if ! printf '%s' "$ID" | grep -Eq '^[a-z0-9][a-z0-9-]{2,30}$'; then
  echo "✗ tenant_id không hợp lệ: $ID" >&2; exit 1
fi
# Chặn xoá nhầm DB hệ thống / template / demo dùng chung.
case "$ID" in
  postgres|template0|template1|odoo|demo|sapiones_tpl)
    echo "✗ TỪ CHỐI: '$ID' là DB được bảo vệ." >&2; exit 1;;
esac

echo "→ Drop DB '$ID'"
$DC exec -T db bash -lc 'dropdb -U "${POSTGRES_USER:-odoo}" --force --if-exists '"$ID" \
  && echo "  ✓ DB dropped"

echo "→ Xoá filestore '$ID'"
$DC exec -T odoo bash -lc 'rm -rf "/var/lib/odoo/filestore/'"$ID"'"' \
  && echo "  ✓ filestore removed (nếu có)"

# CF DNS: đọc creds AN TOÀN (KHÔNG `source` — .env có MAIL_FROM chứa <> làm vỡ bash).
ENV_FILE="${SAPIONES_ENV:-provision-api/.env}"
_envget() { { [ -f "$ENV_FILE" ] && grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\042\047\r'; } || true; }
CF_API_TOKEN="${CF_API_TOKEN:-$(_envget CF_API_TOKEN)}"
CF_ZONE_ID="${CF_ZONE_ID:-$(_envget CF_ZONE_ID)}"
BASE_DOMAIN="${BASE_DOMAIN:-$(_envget BASE_DOMAIN)}"; BASE_DOMAIN="${BASE_DOMAIN:-sapiones.com}"

echo "→ Xoá CF DNS '$ID.$BASE_DOMAIN'"
if [ -n "$CF_API_TOKEN" ] && [ -n "$CF_ZONE_ID" ]; then
  REC=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$ID.$BASE_DOMAIN" \
    | grep -oE '"id":"[a-f0-9]{32}"' | head -1 | cut -d'"' -f4) || true
  if [ -n "${REC:-}" ]; then
    curl -s -X DELETE -H "Authorization: Bearer $CF_API_TOKEN" \
      "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$REC" >/dev/null \
      && echo "  ✓ DNS record đã xoá ($REC)"
  else
    echo "  (không tìm thấy DNS record — có thể đã xoá trước đó)"
  fi
else
  echo "  ⚠ thiếu CF_API_TOKEN/CF_ZONE_ID → xoá thủ công '$ID.$BASE_DOMAIN' trên Cloudflare."
fi

echo "✅ Đã deprovision '$ID'"

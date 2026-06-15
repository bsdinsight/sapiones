#!/usr/bin/env bash
# Sapiones — sao lưu TẤT CẢ database tenant (pg_dump -Fc) + filestore Odoo.
# Mỗi DB → 1 file dump + 1 file filestore.tar.gz. Giữ cục bộ KEEP_DAYS ngày,
# (tùy chọn) đẩy offsite qua rclone (R2/B2/S3). Chạy hằng đêm qua systemd timer.
#
# Biến môi trường (đặt trong deploy/backup.env hoặc systemd EnvironmentFile):
#   BACKUP_DIR     thư mục backup cục bộ            (mặc định /root/backups)
#   KEEP_DAYS      số ngày giữ cục bộ               (mặc định 7)
#   RCLONE_REMOTE  remote rclone, vd "r2:sapiones-backups" (rỗng = không đẩy offsite)
#   SAPIONES_REPO  repo                             (mặc định /root/sapiones)
set -euo pipefail

REPO="${SAPIONES_REPO:-/root/sapiones}"
DB_CONTAINER="${DB_CONTAINER:-sapiones-db}"
ODOO_CONTAINER="${ODOO_CONTAINER:-sapiones-odoo}"
PGUSER="${PGUSER:-odoo}"
BACKUP_DIR="${BACKUP_DIR:-/root/backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"
RCLONE_REMOTE="${RCLONE_REMOTE:-}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DAY="$(date +%Y%m%d)"

log(){ echo "[$(date +%H:%M:%S)] $*"; }
mkdir -p "$BACKUP_DIR"

# DB cần sao lưu: bỏ 'postgres' + template. Bao gồm sapiones_tpl, demo, mọi tenant.
DBS=$(docker exec "$DB_CONTAINER" psql -U "$PGUSER" -d postgres -At \
  -c "SELECT datname FROM pg_database WHERE datistemplate=false AND datname<>'postgres' ORDER BY datname;")
[ -z "$DBS" ] && { log "Không có DB nào để backup"; exit 0; }

# Thư mục filestore trong container odoo (Odoo 19: /var/lib/odoo/filestore/<db>).
FS_ROOT=$(docker exec "$ODOO_CONTAINER" sh -c \
  'for d in /var/lib/odoo/filestore /var/lib/odoo/.local/share/Odoo/filestore; do [ -d "$d" ] && { echo "$d"; break; }; done' || true)

n=0
for db in $DBS; do
  out="$BACKUP_DIR/$db"; mkdir -p "$out"
  log "[$db] pg_dump…"
  docker exec "$DB_CONTAINER" pg_dump -U "$PGUSER" -Fc "$db" > "$out/$db-$STAMP.dump"
  if [ -n "$FS_ROOT" ] && docker exec "$ODOO_CONTAINER" test -d "$FS_ROOT/$db" 2>/dev/null; then
    log "[$db] filestore…"
    docker exec "$ODOO_CONTAINER" tar -C "$FS_ROOT" -czf - "$db" > "$out/$db-$STAMP-filestore.tar.gz"
  fi
  n=$((n+1))
done
log "Đã backup $n DB → $BACKUP_DIR"

# Dọn bản cũ cục bộ — CHỈ trong thư mục các DB script này quản lý.
# (/root/backups có thể dùng chung với hệ thống backup khác — KHÔNG quét toàn bộ.)
for db in $DBS; do
  find "$BACKUP_DIR/$db" -maxdepth 1 -type f \( -name '*.dump' -o -name '*-filestore.tar.gz' \) -mtime +"$KEEP_DAYS" -delete 2>/dev/null || true
done

# Đẩy offsite (nếu cấu hình rclone).
if [ -n "$RCLONE_REMOTE" ]; then
  if command -v rclone >/dev/null 2>&1; then
    log "Đẩy offsite → $RCLONE_REMOTE/$DAY"
    rclone copy "$BACKUP_DIR" "$RCLONE_REMOTE/$DAY" --transfers 4 --no-traverse
    # Dọn offsite cũ hơn KEEP_DAYS ngày.
    rclone delete "$RCLONE_REMOTE" --min-age "${KEEP_DAYS}d" --rmdirs 2>/dev/null || true
  else
    log "CẢNH BÁO: RCLONE_REMOTE đặt nhưng chưa cài rclone — bỏ qua offsite"
  fi
fi
log "HOÀN TẤT."

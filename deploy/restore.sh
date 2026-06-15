#!/usr/bin/env bash
# Sapiones — phục hồi MỘT database tenant từ backup do backup.sh tạo.
#
# Dùng:
#   restore.sh <file.dump> <target_db> [file-filestore.tar.gz]
#   restore.sh --test <file.dump>            # phục hồi thử ra DB tạm rồi xoá (kiểm tra dump còn tốt)
#
# Lưu ý: target_db phải CHƯA tồn tại. Nếu phục hồi đè tenant đang chạy, dừng truy
# cập tenant đó trước. Filestore giải nén vào tên thư mục = target_db.
set -euo pipefail

DB_CONTAINER="${DB_CONTAINER:-sapiones-db}"
ODOO_CONTAINER="${ODOO_CONTAINER:-sapiones-odoo}"
PGUSER="${PGUSER:-odoo}"
FS_ROOT="${FS_ROOT:-/var/lib/odoo/filestore}"

psql(){ docker exec "$DB_CONTAINER" psql -U "$PGUSER" -d postgres "$@"; }

# --- Chế độ TEST: phục hồi ra DB tạm, đếm bảng, rồi xoá ---
if [ "${1:-}" = "--test" ]; then
  DUMP="${2:?cần file .dump}"
  T="restoretest_$(date +%s)"
  echo "→ Test phục hồi '$DUMP' ra DB tạm '$T'…"
  psql -c "CREATE DATABASE \"$T\";" >/dev/null
  trap 'psql -c "DROP DATABASE IF EXISTS \"'"$T"'\";" >/dev/null 2>&1 || true' EXIT
  docker exec -i "$DB_CONTAINER" pg_restore -U "$PGUSER" -d "$T" --no-owner --no-acl < "$DUMP" 2>/tmp/restore.err || {
    echo "⚠️  pg_restore báo lỗi (xem /tmp/restore.err — cảnh báo --no-owner thường vô hại):"; tail -5 /tmp/restore.err; }
  TBL=$(psql -At -d "$T" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "?")
  RES=$(docker exec "$DB_CONTAINER" psql -U "$PGUSER" -At -d "$T" -c "SELECT count(*) FROM res_users;" 2>/dev/null || echo "?")
  echo "✓ Phục hồi OK — $TBL bảng, $RES người dùng. DB tạm sẽ được xoá."
  exit 0
fi

# --- Phục hồi THẬT ---
DUMP="${1:?cần file .dump}"; TARGET="${2:?cần tên target_db}"; FS="${3:-}"
if psql -At -c "SELECT 1 FROM pg_database WHERE datname='$TARGET';" | grep -q 1; then
  echo "✗ DB '$TARGET' đã tồn tại — chọn tên khác hoặc xoá trước."; exit 2
fi
echo "→ Tạo DB '$TARGET' + phục hồi dữ liệu…"
psql -c "CREATE DATABASE \"$TARGET\" OWNER \"$PGUSER\";" >/dev/null
docker exec -i "$DB_CONTAINER" pg_restore -U "$PGUSER" -d "$TARGET" --no-owner --no-acl < "$DUMP"
if [ -n "$FS" ]; then
  echo "→ Phục hồi filestore vào '$FS_ROOT/$TARGET'…"
  TMP="/tmp/fs_$$"; docker exec "$ODOO_CONTAINER" mkdir -p "$FS_ROOT" "$TMP"
  docker exec -i "$ODOO_CONTAINER" tar -C "$TMP" -xzf - < "$FS"
  # Thư mục trong tar tên theo DB gốc → đổi thành target.
  docker exec "$ODOO_CONTAINER" sh -c "src=\$(ls $TMP | head -1); rm -rf '$FS_ROOT/$TARGET'; mv \"$TMP/\$src\" '$FS_ROOT/$TARGET'; rmdir $TMP 2>/dev/null || true"
fi
echo "✓ Xong. Tenant '$TARGET' đã phục hồi. (Nếu là bản test/staging, cân nhắc 'odoo neutralize' trước khi chạy.)"

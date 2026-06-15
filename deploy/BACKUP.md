# Sapiones — Sao lưu & Phục hồi tenant

Sao lưu **tất cả** database (`sapiones_tpl`, `demo`, mọi tenant) bằng `pg_dump -Fc`
+ **filestore** Odoo (ảnh, PDF phiếu lương, đính kèm). Giữ cục bộ `KEEP_DAYS` ngày
+ (khuyến nghị) đẩy **offsite** qua rclone → Cloudflare R2.

> ⚠️ Backup chỉ nằm trên VPS = KHÔNG an toàn (VPS chết là mất). Bật offsite trước
> khi nhận khách thật.

## Cài đặt (1 lần trên VPS)
```bash
cd /root/sapiones && git pull
chmod +x deploy/backup.sh deploy/restore.sh

# (tùy chọn) chỉnh thư mục/giữ-ngày/offsite
cp deploy/backup.env.example deploy/backup.env && nano deploy/backup.env

# systemd timer — chạy 02:30 hằng đêm
cp deploy/sapiones-backup.service deploy/sapiones-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sapiones-backup.timer
systemctl list-timers sapiones-backup.timer
```

## Chạy thử ngay
```bash
/root/sapiones/deploy/backup.sh
ls -lhR /root/backups
```

## Test phục hồi (xác nhận dump dùng được — KHÔNG đụng dữ liệu thật)
```bash
DUMP=$(ls -t /root/backups/demo/demo-*.dump | head -1)
/root/sapiones/deploy/restore.sh --test "$DUMP"
# → "Phục hồi OK — N bảng, M người dùng", DB tạm tự xoá
```

## Phục hồi thật (khôi phục 1 tenant)
```bash
DUMP=/root/backups/<id>/<id>-<stamp>.dump
FS=/root/backups/<id>/<id>-<stamp>-filestore.tar.gz
/root/sapiones/deploy/restore.sh "$DUMP" <id> "$FS"   # target_db phải CHƯA tồn tại
```

## Offsite — Cloudflare R2
1. CF dashboard → **R2** → tạo bucket `sapiones-backups`
2. R2 → **Manage API Tokens** → token *Object Read & Write* → lưu Access Key + Secret + endpoint `https://<acct>.r2.cloudflarestorage.com`
3. Cài + cấu hình rclone (remote kiểu **Amazon S3**, provider **Cloudflare**):
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   rclone config      # n → tên 'r2' → s3 → Cloudflare → điền key/secret/endpoint, region: auto
   ```
4. `deploy/backup.env`: bỏ comment `RCLONE_REMOTE=r2:sapiones-backups`
5. Chạy lại `deploy/backup.sh` → kiểm tra `rclone ls r2:sapiones-backups`

## Khôi phục từ offsite
```bash
rclone copy r2:sapiones-backups/<YYYYMMDD> /root/restore-tmp
# rồi dùng restore.sh như trên với file trong /root/restore-tmp
```

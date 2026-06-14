# Sapiones — Triển khai VPS (hosted multi-tenant)

Mô hình: **BSD host sẵn trên VPS**, khách đăng ký → tự tạo DB → vào chạy ngay (không cài gì).
1 Postgres + 1 Odoo phục vụ nhiều DB, route theo subdomain (`dbfilter=^%d$`), trước mặt là
**1 Cloudflare Tunnel** (cloudflared làm reverse proxy luôn — không cần nginx/caddy).

```
<khach>.sapiones.com ──CF proxy──> CF Tunnel ──ingress *──> odoo:8069 ──dbfilter──> DB "<khach>"
register.sapiones.com    ──CF proxy──> CF Tunnel ──ingress────> <BIND_HOST>:8088 (provision-api trên host)
```

## 0. Chuẩn bị
- VPS Linux + Docker + docker compose. DNS `sapiones.com` quản lý bởi Cloudflare.
- Clone 2 repo (enterprise là sibling — đường dẫn `../sapiones-enterprise` trong compose):
```bash
cd /root
git clone https://github.com/bsdinsight/sapiones
git clone https://github.com/bsdinsight/sapiones-enterprise   # module trả phí (private)
cd /root/sapiones
cp deploy/.env.example .env                       # điền POSTGRES_PASSWORD + TUNNEL_TOKEN
cp deploy/odoo.conf.example deploy/odoo.conf      # đổi admin_passwd mạnh
chmod 644 deploy/odoo.conf
```

## 1. Khởi động Postgres + Odoo (chưa expose)
```bash
docker compose -f docker-compose.vps.yml up -d db odoo
```

## 2. Dựng DB template `sapiones_tpl`
Xem `demo-data/packs/README.md` — cài full module + `--load-language=vi_VN --without-demo=all`,
rồi nạp `pack_sapiones.py`. Làm lại mỗi khi cập nhật module.

## 3. Cloudflare Tunnel
1. Zero Trust → Networks → Tunnels → tạo tunnel **"sapiones"** → copy token → `.env` (`TUNNEL_TOKEN=`).
2. Bật cloudflared:
```bash
docker compose -f docker-compose.vps.yml --profile tunnel up -d
```
3. **Public hostnames (ingress)** của tunnel:
   - `*.sapiones.com` → Service `http://odoo:8069`  ← wildcard ingress, mọi tenant dùng chung 1 route
   - `register.sapiones.com` → Service `http://<BIND_HOST>:8088`  ← provision-api (host)
   > ⚠️ Wildcard ingress chỉ match khi cloudflared MỚI. Nếu trả 404 (server: cloudflare):
   > `docker compose --profile tunnel pull cloudflared && up -d --force-recreate cloudflared`
   > (force-recreate KHÔNG tự pull image!)
4. **DNS**: tạo proxied CNAME `register.sapiones.com → <tunnel-uuid>.cfargotunnel.com`. Subdomain
   tenant `<id>.sapiones.com` thì provision-api **tự tạo** qua CF API (gói Free không proxy
   được wildcard DNS — phải tạo từng record; ingress wildcard thì OK mọi gói).
5. **SSL**: Universal SSL phủ apex + **1 cấp** wildcard → `<id>.sapiones.com` OK. ĐỪNG dùng 2 cấp.

## 4. provision-api (đăng ký tự động)
Xem `provision-api/README.md` — venv + systemd, `.env` (SMTP Resend + CF token + BIND_HOST),
mở `ufw` cho subnet docker.

## 5. Tạo tenant
- Tự động: khách điền form `sapiones.com/dang-ky` → provision-api lo hết.
- Thủ công: `./demo-data/packs/provision.sh <id> <email> "<công ty>" "<liên hệ>" "<tỉnh>" <sđt>`

## 6. Nâng cấp module cho tenant ĐANG chạy
Tenant clone từ template tại thời điểm tạo → KHÔNG tự cập nhật. Khi ra module mới:
```bash
# 1) cập nhật template
docker compose -f docker-compose.vps.yml exec -T odoo \
  odoo -d sapiones_tpl -u <module> --stop-after-init --db_host=db --db_user=odoo --db_password=$PW
# 2) cập nhật từng tenant (script lặp qua các DB)
for db in $(docker compose exec -T db psql -U odoo -d postgres -tAc \
  "SELECT datname FROM pg_database WHERE datname ~ '^[0-9]{6}$'"); do
  docker compose -f docker-compose.vps.yml exec -T odoo \
    odoo -d "$db" -u <module> --stop-after-init --db_host=db --db_user=odoo --db_password=$PW
done
```

## 7. Gotchas (đã đúc kết từ Agrione)
| Triệu chứng | Nguyên nhân | Fix |
|---|---|---|
| `1033` | DNS trỏ tunnel không có connector | bật cloudflared; đừng tạo 2 tunnel trùng tên |
| Treo (không trả) | routing OK nhưng origin không tới | mở `ufw` cho subnet docker → port provision-api |
| `404 server:cloudflare` | ingress wildcard không khớp (cloudflared cũ) | `pull` rồi `up -d --force-recreate cloudflared` |
| provision-api không tới | bind sai host | bind **IP gateway** docker network, KHÔNG 127.0.0.1 |
| systemd đọc sai env | comment cùng dòng trong `.env` | để comment DÒNG RIÊNG |
| Thông báo realtime không chạy | longpolling/websocket | `proxy_mode=True` (CF proxy WS sẵn); workers thấp thì 8069 lo |

## 8. Backup
`pg_dump` từng DB tenant định kỳ (cron) + `data/` (filestore). Mỗi tenant 1 DB → backup/restore độc lập.

## Mapping với mảnh khác của Sapiones
- **Mobile app**: `EXPO_PUBLIC_API_URL=https://<khach>.sapiones.com` (build/run theo từng khách),
  QR onboarding nhúng URL này.
- **Jobboard connector**: instance hosted của khách = "on-prem" cũ → connector push lên board trung tâm như cũ.
- **License Ed25519**: gói trả phí truyền `TENANT_LICENSE='SAP1...'` lúc provision (xem `provision_setup.py`).

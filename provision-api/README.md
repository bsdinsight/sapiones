# Sapiones Provisioning API

FastAPI nhỏ chạy **trên HOST** của VPS, biến form `sapiones.com/dang-ky` thành tenant
chạy được: xác thực email → clone DB template → tạo DNS Cloudflare. ~10–20s, không thao tác tay.

## Endpoint (khớp form BSD Website)
- `POST /v1/register/start` `{email,name,company,province,phone}` → gửi **mã 6 số** qua email → `{request_id}`
- `POST /v1/register/verify` `{request_id,code,password}` → provision → `{tenant_id, url}`
- `GET /v1/health`

## Cài trên VPS
```bash
cd /root/sapiones/provision-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env        # điền SMTP (Resend) + CF token + BIND_HOST
sudo cp sapiones-provision-api.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now sapiones-provision-api
```

## BIND_HOST — quan trọng
provision-api bind vào **IP gateway của docker network `sapiones_default`** (vd `172.18.0.1`),
KHÔNG `0.0.0.0` (khỏi lộ port ra internet) và KHÔNG `127.0.0.1` (cloudflared trong container
không tới được localhost của host). Lấy IP:
```bash
docker network inspect sapiones_default --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'
```
Nếu VPS bật `ufw` (default deny) → mở cho subnet docker:
```bash
ufw allow from 172.18.0.0/16 to any port 8088 proto tcp
```

## Cloudflare
- Tunnel **ingress** thêm route `api.sapiones.com → http://<BIND_HOST>:8088` (api chạy trên host)
  và route `*.sapiones.com → http://odoo:8069` (wildcard ingress — mọi gói đều dùng được).
- DNS: tạo proxied CNAME `api.sapiones.com → <tunnel-uuid>.cfargotunnel.com`. Mỗi tenant,
  app tự tạo CNAME `<id>.sapiones.com` qua CF API (token Zone.DNS:Edit cho sapiones.com).

## Test
```bash
curl -s http://<BIND_HOST>:8088/v1/health
curl -s -X POST https://api.sapiones.com/v1/register/start \
  -H 'Content-Type: application/json' \
  -d '{"email":"ban@congty.vn","name":"Chị Lan","company":"Công ty May ABC"}'
```

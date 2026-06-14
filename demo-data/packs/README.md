# Sapiones — Template & Provisioning packs

Mô hình **hosted multi-tenant**: 1 Postgres + 1 Odoo phục vụ nhiều DB, mỗi khách = 1 DB,
route theo subdomain (`dbfilter=^%d$`). Tenant tạo bằng cách **clone DB template** —
vài giây, không cần cài lại module.

## 1. Dựng DB template `sapiones_tpl` (1 lần, khi cập nhật module thì làm lại)

```bash
cd /root/sapiones
PW=$(grep -E '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)

# a) Cài full bộ module + tiếng Việt, KHÔNG demo
docker compose -f docker-compose.vps.yml exec -T odoo \
  odoo -d sapiones_tpl \
  -i l10n_vn_hr,sapiones_payroll_vn,sapiones_shift_vn,sapiones_ess,sapiones_recruitment_vn,sapiones_knowledge_vn,sapiones_performance_vn,sapiones_hr_certificate,sapiones_mobile_api,sapiones_workplan,sapiones_license,brand \
  --without-demo=all --load-language=vi_VN --stop-after-init \
  --db_host=db --db_user=odoo --db_password="$PW"

# b) Nạp Knowledge Pack (danh mục HR dùng chung) — idempotent
docker compose -f docker-compose.vps.yml exec -T odoo bash -lc '
  odoo shell -d sapiones_tpl --db_host="$HOST" --db_user="$USER" \
    --db_password="$PASSWORD" --no-http' < demo-data/packs/pack_sapiones.py
```

> Sau này thêm/sửa module: chạy lại (a) với `-u <module>` trên `sapiones_tpl`, rồi (b).
> Tenant CŨ không tự cập nhật theo template — nâng cấp tenant cũ bằng `-u` riêng (xem DEPLOY.md).

## 2. Tạo 1 tenant (thủ công — bình thường provision-api tự gọi)

```bash
./demo-data/packs/provision.sh 412345 hr@congtyabc.vn "Công ty May ABC" "Chị Lan" "Bình Dương" 0905123456
# Mật khẩu chủ:   TENANT_PASSWORD=... ./provision.sh ...
# License trả phí: TENANT_LICENSE='SAP1....' ./provision.sh ...
```

→ tạo DB `412345` (clone `sapiones_tpl`) + đặt công ty/chủ/license. Truy cập
`https://412345.sapiones.com` (cần DNS record — provision-api tự tạo qua CF API).

## File
- `pack_sapiones.py` — danh mục HR nền (chức danh, ca, loại nghỉ, loại chứng chỉ). No demo, idempotent.
- `provision.sh` — clone template → tenant DB + hậu xử lý. Exit 2 nếu id trùng.
- `provision_setup.py` — đặt công ty/chủ (login=email)/license/tắt mail, chạy qua `odoo shell`.

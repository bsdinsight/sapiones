# -*- coding: utf-8 -*-
"""Hậu xử lý 1 tenant MỚI (clone từ template sapiones_tpl) — chạy bằng odoo shell.

Đọc tham số qua biến môi trường (provision.sh truyền vào):
  TENANT_COMPANY   tên công ty (hiển thị)
  TENANT_EMAIL     email chủ tài khoản (dùng làm LOGIN — xác thực qua email)
  TENANT_NAME      tên người liên hệ (admin display name)
  TENANT_PASSWORD  mật khẩu chủ đặt lúc đăng ký (tuỳ chọn)
  TENANT_PHONE     SĐT liên hệ (tuỳ chọn)
  TENANT_PROVINCE  tỉnh/thành (tuỳ chọn)
  TENANT_LICENSE   mã bản quyền Ed25519 (tuỳ chọn — gói trả phí; trống = bản free)

Việc: đặt tên công ty (VN/VND) + admin = chủ (login EMAIL) + nạp license (nếu có) +
neutralize nhẹ (tắt mail server kế thừa từ template).
Defensive: lỗi phụ KHÔNG làm hỏng tenant (tài khoản vẫn dùng được).
"""
import os

COMPANY = (os.environ.get('TENANT_COMPANY') or 'Công ty của tôi').strip()
EMAIL = (os.environ.get('TENANT_EMAIL') or '').strip()
NAME = (os.environ.get('TENANT_NAME') or COMPANY).strip()
PASSWORD = (os.environ.get('TENANT_PASSWORD') or '').strip()
PHONE = (os.environ.get('TENANT_PHONE') or '').strip()
PROV = (os.environ.get('TENANT_PROVINCE') or '').strip()
LICENSE = (os.environ.get('TENANT_LICENSE') or '').strip()

print("=" * 60)
print("PROVISION TENANT:", COMPANY, "| email:", EMAIL, "| tỉnh:", PROV or '—')
print("=" * 60)

# 1) Công ty = tên khách (VN + VND)
company = env.company
company.name = COMPANY
vn = env.ref('base.vn', raise_if_not_found=False)
if vn:
    try:
        company.country_id = vn.id
        vnd = env['res.currency'].search([('name', '=', 'VND')], limit=1)
        if vnd:
            company.currency_id = vnd.id
    except Exception as e:
        print("  (lỗi set country/currency:", e, ")")
print("  ✓ Công ty →", COMPANY)

# 2) Admin = chủ (login = EMAIL; xác thực qua email khi đăng ký)
admin = env.ref('base.user_admin', raise_if_not_found=False)
if admin and EMAIL:
    vals = {'name': NAME, 'login': EMAIL, 'email': EMAIL}
    if PASSWORD:
        vals['password'] = PASSWORD
    # Home Action = Trang Tổng quan (nếu đã cài dashboard) → đăng nhập vào thẳng, không rơi Discuss.
    dash = env.ref('sapiones_dashboard.action_sapiones_dashboard', raise_if_not_found=False)
    if dash:
        vals['action_id'] = dash.id
    try:
        admin.write(vals)
    except Exception as e:
        print("  (lỗi set login, giữ cũ:", e, ")")
    if admin.partner_id:
        admin.partner_id.write({'name': NAME, 'email': EMAIL, 'phone': PHONE or False})
    print("  ✓ Chủ →", NAME, "(login email:", EMAIL, ")")

# 3) License — gói trả phí thì nạp key Ed25519; trống = bản free (≤ hạn mức miễn phí)
if LICENSE and 'sapiones.license' in env:
    try:
        lic = env['sapiones.license'].sudo()._get() if hasattr(env['sapiones.license'], '_get') \
            else (env['sapiones.license'].sudo().search([], limit=1) or env['sapiones.license'].sudo().create({}))
        lic.write({'license_key': LICENSE})
        lic.invalidate_recordset()
        print("  ✓ License nạp xong → trạng thái:", lic.state)
    except Exception as e:
        print("  (lỗi nạp license, để bản free:", e, ")")
else:
    print("  ✓ Bản free (chưa có license key)")

# 4) Neutralize nhẹ: tắt mail server outgoing kế thừa từ template
ms = env['ir.mail_server'].search([])
if ms:
    ms.write({'active': False})
    print("  ✓ Tắt %d mail server (neutralize)" % len(ms))

env.cr.commit()
print("\n✅ TENANT READY —", COMPANY, "| đăng nhập email:", EMAIL)

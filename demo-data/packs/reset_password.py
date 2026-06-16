# -*- coding: utf-8 -*-
"""Đặt lại mật khẩu admin của MỘT tenant — chạy bằng odoo shell.
Env: TENANT_EMAIL (login), TENANT_PASSWORD (mật khẩu mới).
In RESET_OK nếu tìm thấy user theo login & đổi xong; RESET_FAIL nếu không."""
import os

EMAIL = (os.environ.get('TENANT_EMAIL') or '').strip()
PASSWORD = (os.environ.get('TENANT_PASSWORD') or '').strip()

ok = False
if EMAIL and PASSWORD:
    try:
        u = env['res.users'].sudo().search([('login', '=', EMAIL)], limit=1)
        if u:
            u.write({'password': PASSWORD})
            env.cr.commit()
            ok = True
    except Exception as e:
        print("RESET_ERR:", e)

print("RESET_OK" if ok else "RESET_FAIL")

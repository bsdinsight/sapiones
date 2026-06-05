# -*- coding: utf-8 -*-
"""Seed chứng chỉ demo cho các nhân viên đã có (mix còn hạn / sắp hết / hết hạn).
Chạy: docker exec -i sapiones-odoo bash -lc 'odoo shell -d sapiones --db_host=$HOST --db_user=$USER --db_password=$PASSWORD --no-http' < seed_demo_certificates.py
Idempotent: bỏ qua nếu đã có chứng chỉ.
"""
from datetime import date, timedelta


def run(env):
    C = env['sapiones.hr.certificate']
    if C.search_count([]):
        print('Đã có chứng chỉ — bỏ qua.')
        return
    T = env['sapiones.hr.certificate.type']
    types = {t.code: t for t in T.search([])}
    today = date.today()
    offsets = [-30, -90, 20, 45, 300, 500, 600, 800]  # mix: hết hạn / sắp hết / còn hạn

    vals = []
    oi = 0
    for e in env['hr.employee'].search([('base_wage', '>', 0)]):
        dept = e.department_id.name or ''
        title = e.job_title or ''
        codes = ['ATVSLD']  # ai cũng có ATVSLĐ
        if 'Xưởng' in dept or 'Công nhân' in title or 'Tổ trưởng' in title or 'Quản đốc' in title:
            codes.append('XENANG')
        if 'Kỹ thuật' in dept:
            codes += ['ANDIEN', 'HAN']
        if 'Kinh doanh' in dept or 'Kế toán' in dept or 'Giám đốc' in title:
            codes.append('NGOAINGU')
        for code in codes:
            t = types.get(code)
            if not t:
                continue
            months = t.default_validity_months or 24
            exp = today + timedelta(days=offsets[oi % len(offsets)])
            oi += 1
            vals.append({
                'name': t.name,
                'employee_id': e.id,
                'type_id': t.id,
                'number': '%s-%04d' % (code, e.id),
                'issuing_organization': 'Sở LĐ-TB&XH',
                'date_issued': exp - timedelta(days=months * 30),
                'date_expiry': exp,
            })
    C.create(vals)
    env.cr.commit()
    from collections import Counter
    print('Tạo %d chứng chỉ. Trạng thái:' % len(vals))
    print(dict(Counter(c.state for c in C.search([]))))


run(env)

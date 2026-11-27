# -*- coding: utf-8 -*-
"""SEED DEMO — MST cá nhân và Số sổ BHXH cho nhân viên còn trống (dữ liệu minh hoạ, số ngẫu nhiên).

- MST cá nhân: 10 chữ số, đầu '80' (cùng kiểu mẫu có sẵn 8012345678).
- Số sổ BHXH: 10 chữ số, 2 số đầu là mã tỉnh nơi tham gia — '01' (Hà Nội) cho nhân viên thuộc
  nhánh phòng ban có chữ "Hà Nội" / cửa hàng Hoàn Kiếm, Cầu Giấy, Đống Đa; còn lại '79' (TP.HCM).
- Không ghi đè người đã có số; số không trùng trong DB; seed cố định theo id nên chạy lại ra cùng số.
Chạy: odoo shell -d <db> < seed_mst_bhxh.py
"""
import random

Emp = env['hr.employee'].sudo().with_context(active_test=False, tracking_disable=True, mail_notrack=True)
emps = Emp.search([], order='id')
used_tax = set(e.vn_tax_code for e in emps if e.vn_tax_code)
used_si = set(e.vn_si_code for e in emps if e.vn_si_code)
HN_KEYS = ('Hà Nội', 'Hoàn Kiếm', 'Cầu Giấy', 'Đống Đa')


def province(emp):
    d = emp.department_id
    while d:
        if any(k in (d.name or '') for k in HN_KEYS):
            return '01'
        d = d.parent_id
    return '79'


def gen(rnd, prefix, used):
    while True:
        v = prefix + ''.join(str(rnd.randint(0, 9)) for _ in range(10 - len(prefix)))
        if v not in used:
            used.add(v)
            return v


n_tax = n_si = 0
for e in emps:
    rnd = random.Random('%s-%s' % (env.cr.dbname, e.id))
    vals = {}
    if not e.vn_tax_code:
        vals['vn_tax_code'] = gen(rnd, '80', used_tax)
        n_tax += 1
    if not e.vn_si_code:
        vals['vn_si_code'] = gen(rnd, province(e), used_si)
        n_si += 1
    if vals:
        e.write(vals)

env.cr.commit()
print('Nhân viên:', len(emps), '| điền MST:', n_tax, '| điền số sổ BHXH:', n_si)
print('Còn trống:', Emp.search_count([('vn_tax_code', 'in', (False, ''))]), Emp.search_count([('vn_si_code', 'in', (False, ''))]))

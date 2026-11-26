# -*- coding: utf-8 -*-
"""SEED DEMO — nhân khẩu học & thời gian làm việc cho nhân viên demo (công ty may mặc).

Điền cho mọi nhân viên đang làm: ngày sinh, giới tính (nếu thiếu), hôn nhân, trình độ,
dân tộc, tôn giáo, quê quán, tỉnh/phường thường trú, nơi làm việc, ngày vào làm,
loại hợp đồng, hết thử việc / hết hạn hợp đồng — để bộ lọc Độ tuổi, Thâm niên,
Sinh nhật tháng này, Đang thử việc, Hợp đồng sắp hết hạn… đều có dữ liệu.

Chỉ là DỮ LIỆU MẪU cho demo. Ngẫu nhiên có hạt giống cố định → chạy lại cho cùng kết quả.
Cần l10n_vn_hr >= 19.0.1.2.0.

Run (VPS):
  docker exec -i sapiones-odoo odoo shell -d demo --no-http < demo-data/packs/seed_hr_demography.py
"""
import random
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields

rnd = random.Random(20261125)
today = fields.Date.today()
Emp = env['hr.employee'].sudo()
company = env.company

# ── Nơi làm việc ────────────────────────────────────────
WL = env['hr.work.location'].sudo()


def wl(name, kind='office'):
    rec = WL.search([('name', '=', name)], limit=1)
    return rec or WL.create({'name': name, 'location_type': kind,
                             'address_id': company.partner_id.id})


wl_a = wl('Xưởng A')
wl_b = wl('Xưởng B')
wl_vp = wl('Văn phòng công ty')

# ── Danh mục ────────────────────────────────────────────
VN = env.ref('base.vn')
states = {s.name: s for s in env['res.country.state'].sudo().search([('country_id', '=', VN.id)])}
Ward = env['frm.vn.ward'].sudo()


def pick(weighted):
    items, weights = zip(*weighted)
    return rnd.choices(items, weights=weights)[0]


RESIDENCE = [('TP Hồ Chí Minh', 45), ('Đồng Nai', 20), ('Tây Ninh', 10), ('Vĩnh Long', 5),
             ('Đồng Tháp', 4), ('An Giang', 4), ('Lâm Đồng', 3), ('Đắk Lắk', 3),
             ('Thanh Hóa', 2), ('Nghệ An', 2), ('Hà Nội', 2)]
HOMETOWN = [('Thanh Hóa', 14), ('Nghệ An', 12), ('Hà Tĩnh', 8), ('Quảng Ngãi', 6),
            ('Đắk Lắk', 6), ('An Giang', 8), ('Đồng Tháp', 7), ('Vĩnh Long', 7), ('Cà Mau', 5),
            ('TP Hồ Chí Minh', 10), ('Đồng Nai', 6), ('Hưng Yên', 3), ('Ninh Bình', 3),
            ('Gia Lai', 3), ('Quảng Trị', 2)]
ETHNIC = [('Kinh', 84), ('Hoa', 4), ('Khmer', 5), ('Tày', 3), ('Mường', 2), ('Ê Đê', 2)]
RELIGION = [('Không', 68), ('Phật giáo', 18), ('Công giáo', 10), ('Cao Đài', 2), ('Hoà Hảo', 2)]


def role(emp):
    j = (emp.job_id.name or emp.job_title or '').lower()
    if any(k in j for k in ('giám đốc', 'chief', 'trưởng phòng', 'kế toán trưởng')):
        return 'mgr'
    if any(k in j for k in ('trưởng', 'thủ kho', 'qc', 'consultant', 'developer')):
        return 'lead'
    return 'worker'


# Tuổi theo vai; thâm niên theo vai (năm). Đảm bảo phủ đủ các khoảng.
AGE = {'worker': [(19, 24, 30), (25, 34, 45), (35, 44, 18), (45, 54, 6), (55, 58, 1)],
       'lead': [(28, 34, 30), (35, 44, 45), (45, 54, 20), (55, 58, 5)],
       'mgr': [(35, 44, 40), (45, 54, 45), (55, 59, 15)]}
SEN = {'worker': [(0.05, 0.9, 25), (1, 2.9, 32), (3, 4.9, 20), (5, 9.9, 18), (10, 14, 5)],
       'lead': [(1, 2.9, 15), (3, 4.9, 25), (5, 9.9, 40), (10, 16, 20)],
       'mgr': [(1, 2.9, 10), (3, 4.9, 20), (5, 9.9, 40), (10, 18, 30)]}


def rand_range(spec):
    lo, hi, _w = pick([(s, s[2]) for s in spec])
    return rnd.uniform(lo, hi)


emps = Emp.search([('active', '=', True)], order='id')
print('Nhân viên đang làm:', len(emps))

permanent = env.ref('hr.contract_type_permanent', raise_if_not_found=False)
fixed = env.ref('hr.contract_type_temporary', raise_if_not_found=False)
seasonal = env.ref('hr.contract_type_seasonal', raise_if_not_found=False)

expiring_left = 3        # số HĐ hết hạn trong 30 ngày
birthday_month_left = 4  # số người sinh nhật tháng này
trial_left = 3           # số người đang thử việc
old_left = 2             # số người từ 55 tuổi (quản lý / tổ trưởng)

for i, e in enumerate(emps):
    r = role(e)
    age = rand_range(AGE[r])
    if old_left and r != 'worker' and age >= 45:
        age = rnd.uniform(55.2, 58.5)
        old_left -= 1
    bd = today - timedelta(days=int(age * 365.25))
    if birthday_month_left and i % 9 == 4:
        bd = bd.replace(month=today.month, day=min(bd.day, 28))
        birthday_month_left -= 1
    sen = rand_range(SEN[r])
    # không cho vào làm trước 18 tuổi
    sen = min(sen, max(age - 18.5, 0.1))
    if trial_left and r == 'worker' and i % 7 == 3:
        sen = (20, 33, 45)[3 - trial_left] / 365.25   # mới vào, đang thử việc
        trial_left -= 1
    start = today - timedelta(days=int(sen * 365.25))

    sex = e.sex or (pick([('female', 65), ('male', 35)]) if r == 'worker' else 'male')
    if age < 25:
        marital = pick([('single', 80), ('married', 20)])
    elif age < 35:
        marital = pick([('single', 35), ('married', 65)])
    else:
        marital = pick([('married', 85), ('single', 5), ('divorced', 6), ('widower', 4)])
    cert = {'worker': pick([('other', 70), ('graduate', 30)]),
            'lead': pick([('graduate', 50), ('bachelor', 50)]),
            'mgr': pick([('bachelor', 60), ('master', 40)])}[r]

    st_name = pick(RESIDENCE)
    st = states.get(st_name)
    ward = Ward.search([('state_id', '=', st.id)]) if st else Ward
    ward = rnd.choice(ward) if ward else False

    if r == 'mgr' or (e.department_id.name or '').startswith(('Phòng', 'Ban', 'Quản trị', 'Kho')):
        loc = wl_vp
    elif 'Xưởng B' in (e.department_id.name or ''):
        loc = wl_b
    else:
        loc = wl_a

    vals = {
        'birthday': bd, 'sex': sex, 'marital': marital, 'certificate': cert,
        'vn_ethnicity': pick(ETHNIC), 'vn_religion': pick(RELIGION), 'vn_hometown': pick(HOMETOWN),
        'private_country_id': VN.id, 'private_state_id': st.id if st else False,
        'private_vn_ward_id': ward.id if ward else False,
        'work_location_id': loc.id, 'contract_date_start': start, 'date_join': start,
        'trial_date_end': False, 'contract_date_end': False,
    }
    if sen < 2 / 12:
        # mới vào: còn thử việc 2 tháng (công nhân) — hợp đồng xác định thời hạn 12 tháng
        vals.update(trial_date_end=start + timedelta(days=60),
                    contract_type_id=fixed.id if fixed else False,
                    contract_date_end=start + relativedelta(months=12, days=-1))
    elif sen < 3 or (r == 'worker' and rnd.random() < 0.25):
        # hợp đồng xác định thời hạn 12/36 tháng, kỳ hiện tại còn hiệu lực
        term = 12 if sen < 1 else 36
        end = start + relativedelta(months=term, days=-1)
        while end < today:
            end += relativedelta(months=term)
        if expiring_left and r == 'worker' and sen >= 1:
            end = today + timedelta(days=(7, 15, 25)[3 - expiring_left])
            expiring_left -= 1
        vals.update(contract_type_id=(seasonal if (r == 'worker' and rnd.random() < 0.1) else fixed).id,
                    contract_date_end=end)
    else:
        vals.update(contract_type_id=permanent.id if permanent else False)
    e.write({k: v for k, v in vals.items() if k in e._fields})

    # ── Người phụ thuộc (giảm trừ gia cảnh): NV đã kết hôn từ 27 tuổi, khoảng 60 % có con đăng ký
    if (marital == 'married' and age >= 27 and not e.dependent_ids and rnd.random() < 0.6
            and 'dependent_ids' in e._fields):
        ho = e.name.split()[0]
        for k in range(rnd.choice((1, 1, 2))):
            cb = bd + relativedelta(years=rnd.randint(24, 32), days=rnd.randint(0, 300))
            if cb > today:
                continue
            env['hr.employee.dependent'].sudo().create({
                'employee_id': e.id, 'relationship': 'child',
                'name': '%s %s' % (ho, rnd.choice(['Minh Anh', 'Gia Huy', 'Bảo Ngọc', 'Khánh Linh',
                                                   'Đức Anh', 'Phương Thảo', 'Tuấn Kiệt', 'Ngọc Hân'])),
                'date_birth': cb, 'date_from': max(cb, start).replace(day=1), 'is_registered': True})

# ── Người nước ngoài: 2 chuyên gia (1 người GPLĐ sắp hết hạn trong 60 ngày) ──
FOREIGN = [(('consultant',), 'base.kr', 45), (('developer',), 'base.jp', 300)]
for keys, ctry, days in FOREIGN:
    f = emps.filtered(lambda x: any(k in (x.job_id.name or x.job_title or '').lower() for k in keys))[:1]
    if not f:
        continue
    f.write({'is_foreigner': True, 'country_id': env.ref(ctry).id, 'tax_residency': 'resident',
             'vn_passport': 'M%07d' % rnd.randint(1000000, 9999999),
             'vn_work_permit_no': 'GPLĐ-%04d/%d' % (rnd.randint(100, 9999), today.year - 1),
             'vn_work_permit_expiry': today + timedelta(days=days),
             'vn_visa_expiry': today + timedelta(days=days + 30)})

env.flush_all()
Emp._cron_vn_refresh_demography()
env.cr.commit()

# ── Tóm tắt ─────────────────────────────────────────────
for fname in ('sex', 'vn_age_band', 'vn_seniority_band', 'marital', 'certificate', 'work_location_id'):
    g = Emp._read_group([('active', '=', True)], [fname], ['__count'])
    print(fname, [(str(k), c) for k, c in g])
print('Sinh nhật tháng này:', Emp.search_count([('vn_birth_month', '=', '%02d' % today.month)]))
print('Đang thử việc:', Emp.search_count([('trial_date_end', '>=', today)]))
print('HĐ hết hạn 30 ngày:', Emp.search_count([('contract_date_end', '>=', today),
                                               ('contract_date_end', '<=', today + timedelta(days=30))]))

# -*- coding: utf-8 -*-
"""SEED DEMO F&B — nhân khẩu học & thời gian làm việc (chuỗi cà phê; bản chỉnh từ seed_hr_demography.py).

Khác bản may: lao động trẻ hơn (nhiều sinh viên làm bán thời gian), thâm niên ngắn hơn (nghỉ việc nhiều),
không có chuyên gia nước ngoài; nơi làm việc đã gán ở fnb_01_base.py nên giữ nguyên.

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

rnd = random.Random(20261128)
today = fields.Date.today()
Emp = env['hr.employee'].sudo()
company = env.company

# ── Nơi làm việc ────────────────────────────────────────
WL = env['hr.work.location'].sudo()


def wl(name, kind='office'):
    rec = WL.search([('name', '=', name)], limit=1)
    return rec or WL.create({'name': name, 'location_type': kind,
                             'address_id': company.partner_id.id})


wl_vp = wl('Văn phòng công ty')

# ── Danh mục ────────────────────────────────────────────
VN = env.ref('base.vn')
states = {s.name: s for s in env['res.country.state'].sudo().search([('country_id', '=', VN.id)])}
Ward = env['frm.vn.ward'].sudo()


def pick(weighted):
    items, weights = zip(*weighted)
    return rnd.choices(items, weights=weights)[0]


RESIDENCE_HCM = [('TP Hồ Chí Minh', 80), ('Đồng Nai', 10), ('Tây Ninh', 5), ('Vĩnh Long', 5)]
RESIDENCE_HN = [('Hà Nội', 85), ('Bắc Ninh', 8), ('Hưng Yên', 7)]
HOMETOWN = [('Thanh Hóa', 14), ('Nghệ An', 12), ('Hà Tĩnh', 8), ('Quảng Ngãi', 6),
            ('Đắk Lắk', 6), ('An Giang', 8), ('Đồng Tháp', 7), ('Vĩnh Long', 7), ('Cà Mau', 5),
            ('TP Hồ Chí Minh', 10), ('Đồng Nai', 6), ('Hưng Yên', 3), ('Ninh Bình', 3),
            ('Gia Lai', 3), ('Quảng Trị', 2)]
ETHNIC = [('Kinh', 84), ('Hoa', 4), ('Khmer', 5), ('Tày', 3), ('Mường', 2), ('Ê Đê', 2)]
RELIGION = [('Không', 68), ('Phật giáo', 18), ('Công giáo', 10), ('Cao Đài', 2), ('Hoà Hảo', 2)]


def role(emp):
    j = (emp.job_id.name or emp.job_title or '').lower()
    if any(k in j for k in ('giám đốc', 'trưởng phòng', 'kế toán trưởng', 'quản lý vùng', 'bếp trưởng')):
        return 'mgr'
    if any(k in j for k in ('trưởng', 'bếp chính', 'chuyên viên', 'kế toán', 'qa', 'đào tạo', 'mua hàng')):
        return 'lead'
    if emp.resource_calendar_id.hours_per_day and emp.resource_calendar_id.hours_per_day < 8:
        return 'pt'
    return 'worker'


# Tuổi theo vai; thâm niên theo vai (năm). Đảm bảo phủ đủ các khoảng.
AGE = {'pt': [(18, 21, 55), (22, 24, 35), (25, 30, 10)],
       'worker': [(19, 24, 40), (25, 34, 45), (35, 44, 12), (45, 50, 3)],
       'lead': [(28, 34, 30), (35, 44, 45), (45, 54, 20), (55, 58, 5)],
       'mgr': [(35, 44, 40), (45, 54, 45), (55, 59, 15)]}
SEN = {'pt': [(0.05, 0.5, 45), (0.5, 1.5, 40), (1.5, 2.5, 15)],
       'worker': [(0.05, 0.9, 35), (1, 2.9, 40), (3, 4.9, 17), (5, 8, 8)],
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
    if old_left and r in ('lead', 'mgr') and age >= 45:
        age = rnd.uniform(55.2, 58.5)
        old_left -= 1
    bd = today - timedelta(days=int(age * 365.25))
    if birthday_month_left and i % 9 == 4:
        bd = bd.replace(month=today.month, day=min(bd.day, 28))
        birthday_month_left -= 1
    sen = rand_range(SEN[r])
    # không cho vào làm trước 18 tuổi
    sen = min(sen, max(age - 18.5, 0.1))
    if trial_left and r in ('worker', 'pt') and i % 7 == 3:
        sen = (20, 33, 45)[3 - trial_left] / 365.25   # mới vào, đang thử việc
        trial_left -= 1
    start = today - timedelta(days=int(sen * 365.25))

    sex = e.sex or pick([('female', 60), ('male', 40)])
    if r == 'pt' or age < 25:
        marital = pick([('single', 80), ('married', 20)])
    elif age < 35:
        marital = pick([('single', 35), ('married', 65)])
    else:
        marital = pick([('married', 85), ('single', 5), ('divorced', 6), ('widower', 4)])
    cert = {'pt': pick([('other', 30), ('graduate', 70)]),
            'worker': pick([('other', 60), ('graduate', 40)]),
            'lead': pick([('graduate', 50), ('bachelor', 50)]),
            'mgr': pick([('bachelor', 60), ('master', 40)])}[r]

    hn = 'Hà Nội' in (e.department_id.parent_id.name or '') or e.department_id.name in ('Cửa hàng Hoàn Kiếm', 'Cửa hàng Cầu Giấy', 'Cửa hàng Đống Đa')
    st_name = pick(RESIDENCE_HN if hn else RESIDENCE_HCM)
    st = states.get(st_name)
    ward = Ward.search([('state_id', '=', st.id)]) if st else Ward
    ward = rnd.choice(ward) if ward else False

    loc = e.work_location_id or wl_vp

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
    elif r == 'pt' or sen < 3 or (r == 'worker' and rnd.random() < 0.25):
        # hợp đồng xác định thời hạn 12/36 tháng, kỳ hiện tại còn hiệu lực
        term = 12 if sen < 1 else 36
        end = start + relativedelta(months=term, days=-1)
        while end < today:
            end += relativedelta(months=term)
        if expiring_left and r in ('worker', 'pt') and sen >= 1:
            end = today + timedelta(days=(7, 15, 25)[3 - expiring_left])
            expiring_left -= 1
        vals.update(contract_type_id=fixed.id,
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

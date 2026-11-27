# -*- coding: utf-8 -*-
"""SEED DEMO F&B — nền: công ty, cơ cấu, chức danh, ca làm, nơi làm việc, nhân viên,
chấm công + phiếu lương tháng trước.

Công ty HƯ CẤU "Công ty CP F&B Demo Sapiones": chuỗi cà phê kèm bếp nhẹ, 8 cửa hàng
(5 TP.HCM, 3 Hà Nội) + bếp trung tâm + văn phòng; ~70 nhân viên, ~35–40 % bán thời gian.
Tên người, cửa hàng là dữ liệu minh họa — không trùng thương hiệu thật nào.

Chạy trên DB clone từ sapiones_tpl (chưa có nhân viên). Hạt giống cố định; chạy lại:
bỏ qua nếu đã có nhân viên.
  docker exec -i <odoo> odoo shell -d fnb --no-http < demo-data/packs/fnb/fnb_01_base.py
"""
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields

rnd = random.Random(20261127)
today = fields.Date.today()
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True)
Emp = env['hr.employee'].sudo().with_context(**ctx)
Dept = env['hr.department'].sudo().with_context(**ctx)
Job = env['hr.job'].sudo()
WL = env['hr.work.location'].sudo()
Shift = env['sapiones.shift'].sudo()

if Emp.search_count([]) > 5:
    print('Đã có nhân viên — bỏ qua seed nền F&B.')
    raise SystemExit

# ── Công ty ──────────────────────────────────────────────
company = env.company
vnd = env['res.currency'].with_context(active_test=False).search([('name', '=', 'VND')])
vnd.active = True
company.write({'name': 'Công ty CP F&B Demo Sapiones', 'country_id': env.ref('base.vn').id,
               'currency_id': vnd.id})
env['ir.config_parameter'].sudo().set_param('sapiones_license.free_seats', '100')

# ── Ca làm F&B ───────────────────────────────────────────
SHIFTS = [  # (mã, tên, bắt đầu, kết thúc, nghỉ giữa ca, giá trị công)
    ('FS', 'Ca sáng cửa hàng', 6.0, 14.0, 0.5, 1.0),
    ('FC', 'Ca chiều cửa hàng', 14.0, 22.0, 0.5, 1.0),
    ('FG', 'Ca gãy (10–14h, 17–21h)', 10.0, 21.0, 3.0, 1.0),
    ('PT-S', 'Bán thời gian sáng (4 giờ)', 7.0, 11.0, 0.0, 0.5),
    ('PT-T', 'Bán thời gian tối (4 giờ)', 17.0, 21.0, 0.0, 0.5),
    ('BT', 'Ca bếp trung tâm', 5.0, 13.0, 0.5, 1.0),
]
shift = {}
for code, name, s, e, br, wv in SHIFTS:
    shift[code] = Shift.search([('code', '=', code)], limit=1) or Shift.create(
        {'code': code, 'name': name, 'time_start': s, 'time_end': e, 'break_hours': br, 'work_value': wv})
shift['HC'] = Shift.search([('code', '=', 'HC')], limit=1)
Shift.search([('code', 'in', ('CA1', 'CA2', 'CA3'))]).write({'active': False})  # ca nhà máy

# Lịch bán thời gian 4 giờ/ngày (24 giờ/tuần, 6 ngày) cho nhân viên part-time
Cal = env['resource.calendar'].sudo()
pt_cal = Cal.search([('name', '=', 'Bán thời gian 24 giờ/tuần')], limit=1)
if not pt_cal:
    pt_cal = Cal.create({'name': 'Bán thời gian 24 giờ/tuần', 'hours_per_day': 4.0, 'attendance_ids': [
        (0, 0, {'name': 'T%d' % (d + 2), 'dayofweek': str(d), 'hour_from': 17.0, 'hour_to': 21.0,
                'day_period': 'afternoon'}) for d in range(6)]})
std_cal = Cal.search([], limit=1, order='id')
std_cal.name = 'Toàn thời gian 48 giờ/tuần' if std_cal.name.startswith('Standard') else std_cal.name

# ── Nơi làm việc & cơ cấu ────────────────────────────────
def wl(name, kind='office'):
    return WL.search([('name', '=', name)], limit=1) or WL.create(
        {'name': name, 'location_type': kind, 'address_id': company.partner_id.id})


def dept(name, parent=None):
    d = Dept.search([('name', '=', name)], limit=1)
    return d or Dept.create({'name': name, 'parent_id': parent.id if parent else False})


wl_vp = wl('Văn phòng công ty')
wl_bep = wl('Bếp trung tâm', 'other')
d_bgd = dept('Ban Giám đốc')
d_vh = dept('Khối Vận hành')
d_vhcm = dept('Vùng TP.HCM', d_vh)
d_vhn = dept('Vùng Hà Nội', d_vh)
STORES = [  # (tên cửa hàng, vùng)
    ('Cửa hàng Quận 1', d_vhcm), ('Cửa hàng Quận 3', d_vhcm), ('Cửa hàng Bình Thạnh', d_vhcm),
    ('Cửa hàng Phú Nhuận', d_vhcm), ('Cửa hàng Thủ Đức', d_vhcm),
    ('Cửa hàng Hoàn Kiếm', d_vhn), ('Cửa hàng Cầu Giấy', d_vhn), ('Cửa hàng Đống Đa', d_vhn),
]
store_dept = {n: dept(n, r) for n, r in STORES}
store_wl = {n: wl(n, 'other') for n, _r in STORES}
d_bep = dept('Bếp trung tâm')
d_mh = dept('Mua hàng & Kho')
d_qa = dept('QA An toàn thực phẩm')
d_mkt = dept('Marketing')
d_ns = dept('Nhân sự & Đào tạo')
d_kt = dept('Kế toán')

_jobs = {}


def job(title):
    if title not in _jobs:
        _jobs[title] = Job.search([('name', '=', title)], limit=1) or Job.create({'name': title})
    return _jobs[title]


# ── Tên người (minh họa) ─────────────────────────────────
SUR = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Phan', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô',
       'Dương', 'Lý', 'Đinh', 'Mai', 'Tô', 'Trịnh', 'Cao', 'Đoàn', 'Vương', 'Hà', 'Tạ', 'Chu',
       'Kiều', 'Thái', 'Lâm', 'Trương', 'Lưu', 'Đào']
MID_F = ['Thị', 'Ngọc', 'Thu', 'Thanh', 'Minh', 'Khánh', 'Bảo', 'Phương']
MID_M = ['Văn', 'Minh', 'Quốc', 'Đức', 'Gia', 'Hoàng', 'Thành', 'Tuấn']
GF = ['Anh', 'Trang', 'Linh', 'Vy', 'Hân', 'Ngân', 'Thảo', 'My', 'Uyên', 'Quỳnh', 'Nhi', 'Hà', 'Yến',
      'Hương', 'Mai', 'Lan', 'Châu', 'Tiên', 'Như', 'Giang', 'Phương', 'Diệp', 'Ánh', 'Ly']
GM = ['Huy', 'Khoa', 'Phúc', 'Nam', 'Long', 'Tú', 'Bảo', 'Đạt', 'Khang', 'Vinh', 'Hiếu', 'Kiên',
      'Tâm', 'Lộc', 'Hưng', 'Sơn', 'Quân', 'Trung', 'Thắng', 'Duy', 'Tài', 'Nhân']
used = set()


def person(female):
    for _ in range(200):
        n = '%s %s %s' % (rnd.choice(SUR), rnd.choice(MID_F if female else MID_M), rnd.choice(GF if female else GM))
        if n not in used:
            used.add(n)
            return n
    raise RuntimeError('hết tên')


seq = [0]
META = {}  # id nhân viên → (ca chính, bán thời gian?)


def mk(title, d, wage, female=None, pt=False, loc=None, sh='HC', parent=None):
    seq[0] += 1
    if female is None:
        female = rnd.random() < 0.6
    code = 'FB%04d' % seq[0]
    vals = {'name': person(female), 'barcode': code, 'registration_number': code,
            'sex': 'female' if female else 'male', 'job_id': job(title).id,
            'job_title': title + (' (bán thời gian)' if pt else ''),
            'department_id': d.id, 'base_wage': wage,
            'resource_calendar_id': (pt_cal if pt else std_cal).id,
            'work_location_id': (loc or wl_vp).id,
            'mobile_phone': '0%s %03d %04d' % (rnd.choice(['90', '93', '98', '35', '77', '86']),
                                               rnd.randint(100, 999), rnd.randint(1000, 9999)),
            'parent_id': parent.id if parent else False}
    e = Emp.create({k: v for k, v in vals.items() if k in Emp._fields})
    META[e.id] = (shift[sh], pt)
    return e


# Lương tháng (đ). Bán thời gian: lương tháng quy đổi cho 4 giờ/ngày × 26 ngày (30.000 đ/giờ).
PT_WAGE = 30000 * 4 * 26
staff = []
ceo = mk('Tổng Giám đốc', d_bgd, 45000000, female=False)
coo = mk('Giám đốc Vận hành', d_bgd, 35000000, female=True, parent=ceo)
staff += [ceo, coo]
d_bgd.manager_id = ceo
d_vh.manager_id = coo
rm_hcm = mk('Quản lý vùng', d_vhcm, 25000000, parent=coo)
rm_hn = mk('Quản lý vùng', d_vhn, 24000000, parent=coo)
d_vhcm.manager_id, d_vhn.manager_id = rm_hcm, rm_hn
staff += [rm_hcm, rm_hn]

# 8 cửa hàng — cửa hàng trưởng, ca trưởng, barista, phục vụ, thu ngân, phụ bếp; 3 người bán thời gian/cửa hàng
for i, (sname, region) in enumerate(STORES):
    d, loc = store_dept[sname], store_wl[sname]
    rm = rm_hcm if region == d_vhcm else rm_hn
    big = i in (0, 2, 5)  # cửa hàng lớn: thêm 1 barista + 1 phục vụ
    sm = mk('Cửa hàng trưởng', d, rnd.choice([15000000, 15500000, 16000000]), loc=loc, sh='FG', parent=rm)
    d.manager_id = sm
    team = [sm,
            mk('Ca trưởng', d, rnd.choice([9500000, 10000000]), loc=loc, sh='FC', parent=sm),
            mk('Barista', d, rnd.choice([7500000, 7800000]), loc=loc, sh='FS', parent=sm),
            mk('Phụ bếp', d, 7200000, loc=loc, sh='FS', parent=sm),
            mk('Barista', d, PT_WAGE, pt=True, loc=loc, sh='PT-T', parent=sm),
            mk('Phục vụ', d, PT_WAGE, pt=True, loc=loc, sh='PT-T', parent=sm),
            mk('Thu ngân', d, PT_WAGE, pt=True, loc=loc, sh='PT-S', parent=sm)]
    if big:
        team += [mk('Barista', d, 7500000, loc=loc, sh='FC', parent=sm),
                 mk('Phục vụ', d, PT_WAGE, pt=True, loc=loc, sh='PT-S', parent=sm)]
    staff += team

# Bếp trung tâm
chef = mk('Bếp trưởng', d_bep, 20000000, female=False, loc=wl_bep, sh='BT', parent=coo)
d_bep.manager_id = chef
staff += [chef] + [mk(t, d_bep, w, loc=wl_bep, sh='BT', parent=chef) for t, w in
                   [('Bếp chính', 12000000), ('Bếp chính', 11500000), ('Phụ bếp', 7200000), ('Phụ bếp', 7000000)]]
# Văn phòng
for d, head, members in [
    (d_mh, ('Trưởng phòng Mua hàng', 20000000), [('Nhân viên mua hàng', 11000000), ('Nhân viên kho', 8000000), ('Nhân viên kho', 7800000)]),
    (d_qa, ('Trưởng nhóm QA', 18000000), [('Nhân viên QA', 11000000), ('Nhân viên QA', 10500000)]),
    (d_mkt, ('Trưởng phòng Marketing', 22000000), [('Chuyên viên marketing', 13000000), ('Chuyên viên nội dung', 12000000)]),
    (d_ns, ('Trưởng phòng Nhân sự', 22000000), [('Chuyên viên tuyển dụng', 13000000), ('Đào tạo viên', 13000000), ('Chuyên viên C&B', 13500000)]),
    (d_kt, ('Kế toán trưởng', 24000000), [('Kế toán viên', 12000000), ('Kế toán viên', 11500000)]),
]:
    h = mk(head[0], d, head[1], parent=ceo)
    d.manager_id = h
    staff += [h] + [mk(t, d, w, parent=h, loc=(wl_bep if d == d_mh and 'kho' in t else wl_vp)) for t, w in members]

print('Nhân viên:', len(staff), '· bán thời gian:', sum(1 for e in staff if META[e.id][1]))

# ── Chấm công + phiếu lương tháng trước ──────────────────
Sheet = env['sapiones.attendance.sheet'].sudo().with_context(**ctx)
Slip = env['sapiones.payslip'].sudo().with_context(**ctx)
m0 = (today.replace(day=1) - relativedelta(months=1))
m1 = today.replace(day=1) - timedelta(days=1)
STD = 26.0
for i, e in enumerate(staff):
    sh, pt = META[e.id]
    store = e.department_id.parent_id in (d_vhcm, d_vhn) or e.department_id == d_bep
    worked = STD - rnd.choice([0, 0, 0, 1, 1, 2])
    ot = rnd.choice([0, 0, 4, 8, 12]) if (store and not pt) else 0
    # tăng ca ngày nghỉ (200 %) và lễ (300 %) chỉ rơi vào cửa hàng — mở cửa cả cuối tuần
    ot_we = rnd.choice([0, 0, 0, 8]) if (store and not pt) else 0
    vals = {'employee_id': e.id, 'date_from': m0, 'date_to': m1, 'shift_id': sh.id,
            'standard_days': STD, 'worked_days': worked, 'ot_normal_hours': ot, 'ot_weekend_hours': ot_we,
            'meal_allowance': 730000 if not pt else 0}
    sheet = Sheet.create({k: v for k, v in vals.items() if k in Sheet._fields})
    # phụ cấp chịu thuế: xăng xe 300.000 + chuyên cần 500.000 (đủ công) cho nhân viên toàn thời gian
    allow_tax = 0 if pt else 300000 + (500000 if worked >= STD else 0)
    slip = Slip.create({'employee_id': e.id, 'date_from': m0, 'date_to': m1,
                        'wage': e.base_wage, 'si_base': e.base_wage, 'allowance_taxable': allow_tax,
                        'allowance_exempt': 0 if pt else 730000,
                        'standard_days': STD, 'worked_days': worked,
                        'ot_normal_hours': ot, 'ot_weekend_hours': ot_we})
    slip.action_compute()
    slip.action_done()
    if 'payslip_id' in Sheet._fields:
        sheet.write({'payslip_id': slip.id, 'state': 'confirmed'})
    # tháng này: bảng chấm công nháp (đang chạy)
    Sheet.create({k: v for k, v in dict(vals, date_from=today.replace(day=1),
                                         date_to=today.replace(day=1) + relativedelta(months=1, days=-1),
                                         worked_days=min(today.day - today.day // 7, STD)).items()
                  if k in Sheet._fields})

# Đăng nhập demo công khai: demo / demo (giống demo may)
admin = env.ref('base.user_admin')
admin.write({'login': 'demo', 'password': 'demo', 'name': 'Khách tham quan',
             'tz': 'Asia/Ho_Chi_Minh', 'lang': 'vi_VN'})
dash = env.ref('sapiones_dashboard.action_sapiones_dashboard', raise_if_not_found=False)
if dash:
    admin.action_id = dash.id

env.cr.commit()
print('Phòng ban:', Dept.search_count([]), '· chức danh:', len(_jobs), '· ca:', Shift.search_count([]))
print('Phiếu lương:', Slip.search_count([]), '· bảng chấm công:', Sheet.search_count([]))
print('Quỹ lương tháng %s: %s đ' % (m0.strftime('%m/%Y'), '{:,.0f}'.format(sum(Slip.search([]).mapped('net'))).replace(',', '.')))

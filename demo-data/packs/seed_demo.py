# -*- coding: utf-8 -*-
"""SEED DEMO — đổ dữ liệu mẫu cho workspace demo (demo.sapiones.com).

Chạy trên DB `demo` (đã clone từ sapiones_tpl + provision_setup) để khách dùng thử
thấy hệ thống "sống": nhân viên, phiếu lương (tính thật), chấm công, nghỉ phép,
công việc/lịch, hồ sơ + chứng chỉ, đánh giá KPI/OKR.

Idempotent ở mức thô (tra theo barcode/tên trước khi tạo). Defensive: lỗi 1 phần
KHÔNG làm hỏng cả seed.

Run:
  docker compose -f docker-compose.vps.yml exec -T odoo bash -lc '
    odoo shell -d demo --db_host="$HOST" --db_user="$USER" --db_password="$PASSWORD" --no-http' \
    < demo-data/packs/seed_demo.py
"""
from datetime import date, datetime, timedelta

from odoo import fields

today = fields.Date.today()
first_of_month = today.replace(day=1)


def log(*a):
    print("  ", *a)


def ensure(model, domain, vals):
    M = env[model].sudo()
    rec = M.search(domain, limit=1)
    if not rec:
        f = M._fields
        rec = M.create({k: v for k, v in vals.items() if k in f})
    return rec


# ── Phòng ban ───────────────────────────────────────────
dept_xuong = ensure('hr.department', [('name', '=', 'Chuyền may 3 · Xưởng A')], {'name': 'Chuyền may 3 · Xưởng A'})
dept_kd = ensure('hr.department', [('name', '=', 'Phòng Kinh doanh')], {'name': 'Phòng Kinh doanh'})
shift_sang = env['sapiones.shift'].sudo().search([('code', '=', 'CA-S')], limit=1)

HR = env['hr.employee'].sudo()

# Demo: nới hạn mức nhân viên (free mặc định 20) để demo có nhiều NV + tính lương được.
env['ir.config_parameter'].sudo().set_param('sapiones_license.free_seats', '100')


def mk_emp(name, barcode, idid, sex, job, dept, wage, phone, **extra):
    emp = HR.search([('barcode', '=', barcode)], limit=1)
    vals = {'name': name, 'barcode': barcode, 'identification_id': idid, 'sex': sex,
            'job_title': job, 'department_id': dept.id, 'base_wage': wage, 'mobile_phone': phone}
    vals.update(extra)
    if emp:
        emp.write({k: v for k, v in vals.items() if k in emp._fields})
        return emp
    return HR.create({k: v for k, v in vals.items() if k in HR._fields})


def mk_payslip(emp, wage, piece=0, allow_tax=0, ot=0, night=0):
    Slip = env['sapiones.payslip'].sudo()
    if Slip.search_count([('employee_id', '=', emp.id)]):
        return Slip.search([('employee_id', '=', emp.id)], limit=1)
    slip = Slip.create({
        'employee_id': emp.id, 'date_from': first_of_month,
        'date_to': (first_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1),
        'wage': wage, 'si_base': wage, 'piece_pay': piece, 'allowance_taxable': allow_tax,
        'standard_days': 26, 'worked_days': 24, 'ot_normal_hours': ot, 'night_hours': night,
    })
    slip.action_compute()
    slip.action_done()
    return slip


def mk_attendance(emp, ot=0, night=0, leave_days=0):
    Sheet = env['sapiones.attendance.sheet'].sudo()
    if Sheet.search_count([('employee_id', '=', emp.id)]):
        return
    vals = {'employee_id': emp.id, 'date_from': first_of_month,
            'date_to': (first_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1),
            'standard_days': 26, 'worked_days': 24, 'ot_normal_hours': ot,
            'night_hours': night, 'leave_days': leave_days}
    if shift_sang:
        vals['shift_id'] = shift_sang.id
    Sheet.create({k: v for k, v in vals.items() if k in Sheet._fields})


def mk_cert(emp, name, number, org, expiry):
    if 'sapiones.hr.certificate' not in env:
        return
    Cert = env['sapiones.hr.certificate'].sudo()
    if not Cert.search_count([('employee_id', '=', emp.id), ('name', '=', name)]):
        Cert.create({'employee_id': emp.id, 'name': name, 'number': number,
                     'issuing_organization': org, 'date_issued': today - timedelta(days=400),
                     'date_expiry': expiry})


def mk_work(emp, mgr, items, schedule):
    if 'sapiones.work.item' not in env:
        return
    Item = env['sapiones.work.item'].sudo()
    if not Item.search_count([('employee_id', '=', emp.id)]):
        for nm, cat, tm, proj in items:
            Item.create({'employee_id': emp.id, 'date': today, 'name': nm, 'category': cat,
                         'planned_time': tm, 'project_label': proj, 'assigned_by_id': mgr.id})
    Sched = env['sapiones.work.schedule'].sudo()
    if not Sched.search_count([('employee_id', '=', emp.id)]):
        for i, (typ, label, tm, loc) in enumerate(schedule):
            Sched.create({'employee_id': emp.id, 'date': today + timedelta(days=i), 'type': typ,
                          'label': label, 'time_text': tm, 'location': loc})


def mk_leave(emp, days_from, days_to, reason):
    Lt = env['hr.leave.type'].sudo()
    lt = Lt.search([('name', '=', 'Nghỉ phép năm'), ('requires_allocation', '=', 'yes')], limit=1)
    if not lt:
        vals = {'name': 'Nghỉ phép năm', 'requires_allocation': 'yes'}
        for f in ('allocation_validation_type', 'leave_validation_type'):
            if f in Lt._fields:
                vals[f] = 'no_validation'
        lt = Lt.create(vals)
    Alloc = env['hr.leave.allocation'].sudo()
    if not Alloc.search_count([('employee_id', '=', emp.id), ('holiday_status_id', '=', lt.id)]):
        al = Alloc.create({'name': 'Phép năm', 'employee_id': emp.id,
                           'holiday_status_id': lt.id, 'number_of_days': 12})
        for m in ('action_validate', 'action_approve'):
            if hasattr(al, m):
                try:
                    getattr(al, m)()
                    break
                except Exception:
                    pass
    Leave = env['hr.leave'].sudo()
    if not Leave.search_count([('employee_id', '=', emp.id)]):
        lv = Leave.create({'employee_id': emp.id, 'holiday_status_id': lt.id,
                           'request_date_from': days_from, 'request_date_to': days_to,
                           'name': reason, 'private_name': reason} if 'private_name' in Leave._fields
                          else {'employee_id': emp.id, 'holiday_status_id': lt.id,
                                'request_date_from': days_from, 'request_date_to': days_to, 'name': reason})
        for m in ('action_approve', 'action_validate'):
            if hasattr(lv, m):
                try:
                    getattr(lv, m)()
                    break
                except Exception:
                    pass


def mk_appraisal(emp):
    if 'sapiones.appraisal' not in env:
        return
    Cycle = env['sapiones.appraisal.cycle'].sudo()
    cyc = Cycle.search([('name', '=', 'Quý 2/2026')], limit=1) or Cycle.create(
        {'name': 'Quý 2/2026', 'date_from': '2026-04-01', 'date_to': '2026-06-30', 'state': 'in_progress'})
    Ap = env['sapiones.appraisal'].sudo()
    if Ap.search_count([('employee_id', '=', emp.id)]):
        return
    ap = Ap.create({'cycle_id': cyc.id, 'employee_id': emp.id, 'date_from': '2026-04-01',
                    'date_to': '2026-06-30', 'kpi_ids': [
                        (0, 0, {'name': 'Sản lượng đạt mục tiêu', 'weight': 40, 'target': '≥ 95%', 'result': '97%', 'self_score': 95, 'manager_score': 92}),
                        (0, 0, {'name': 'Chất lượng / tỷ lệ lỗi', 'weight': 35, 'target': '< 2%', 'result': '1.4%', 'self_score': 90, 'manager_score': 88}),
                        (0, 0, {'name': 'Tuân thủ ATLĐ', 'weight': 25, 'target': '100%', 'result': 'Đạt', 'self_score': 100, 'manager_score': 95}),
                    ]})
    for m in ('action_start', 'action_submit_self', 'action_done'):
        try:
            getattr(ap, m)()
        except Exception:
            pass
    Obj = env['sapiones.objective'].sudo()
    if not Obj.search_count([('employee_id', '=', emp.id)]):
        Obj.create({'name': 'Nâng tay nghề & giảm lỗi chuyền may', 'level': 'individual',
                    'employee_id': emp.id, 'date_from': '2026-04-01', 'date_to': '2026-06-30',
                    'key_result_ids': [
                        (0, 0, {'name': 'Hoàn thành khóa kỹ thuật nâng cao', 'target_value': 1, 'current_value': 1, 'uom': 'khóa'}),
                        (0, 0, {'name': 'Giảm tỷ lệ lỗi cá nhân', 'target_value': 100, 'current_value': 70, 'uom': '%'}),
                    ]})


print("=" * 60)
print("SEED DEMO — đổ dữ liệu mẫu cho workspace demo")
print("=" * 60)

mgr = mk_emp('Lê Văn Bình', 'TT00301', 'TT-00301', 'male', 'Tổ trưởng chuyền', dept_xuong, 11000000, '0903330301')
hoa = mk_emp('Nguyễn Thị Hoa', 'CN04821', 'CN-04821', 'female', 'Công nhân may', dept_xuong, 6500000, '0901234318',
             birthday='1995-03-12', marital='married', vn_id_card='036095001234', vn_tax_code='8012345678',
             vn_si_code='0312345678', vn_health_insurance_no='DN4790123456789', vn_hometown='Nam Định',
             vn_ethnicity='Kinh', private_email='hoa.demo@sapiones.com')
minh = mk_emp('Trần Quang Minh', 'VP01307', 'VP-01307', 'male', 'Nhân viên kinh doanh', dept_kd, 16000000, '0902220318')

log("Nhân viên:", HR.search_count([]))

# Hoa — đầy đủ (flagship)
try: mk_payslip(hoa, 6500000, piece=3200000, allow_tax=1800000, ot=18, night=24); log("✓ phiếu lương Hoa")
except Exception as e: log("payslip Hoa:", e)
try: mk_attendance(hoa, ot=18, night=24, leave_days=2); log("✓ chấm công Hoa")
except Exception as e: log("att Hoa:", e)
try:
    mk_work(hoa, mgr,
            [('May công đoạn cổ áo — Đơn #A-203', 'production', 'Trong ca', 'Đơn #A-203 · Áo sơ mi XK'),
             ('Kiểm tra chất lượng lô 45', 'qc', '13:00', 'Kiểm soát chất lượng'),
             ('Vệ sinh, bảo dưỡng máy cuối ca', 'safety', '13:45', 'An toàn lao động')],
            [('shift', 'Ca sáng', '06:00 – 14:00', 'Xưởng A · Chuyền may 3'),
             ('shift', 'Ca sáng', '06:00 – 14:00', 'Xưởng A · Chuyền may 3'),
             ('shift', 'Ca chiều', '14:00 – 22:00', 'Xưởng A')])
    log("✓ công việc + lịch Hoa")
except Exception as e: log("work Hoa:", e)
try: mk_cert(hoa, 'Chứng chỉ An toàn lao động (ATLĐ)', 'ATLD-2024-0481', 'Trung tâm ATLĐ tỉnh', today + timedelta(days=20)); log("✓ chứng chỉ Hoa")
except Exception as e: log("cert Hoa:", e)
try:
    Dep = env['hr.employee.dependent'].sudo()
    if 'dependent_ids' in HR._fields and not Dep.search_count([('employee_id', '=', hoa.id)]):
        dv = {'employee_id': hoa.id, 'name': 'Nguyễn Văn Bin', 'date_birth': '2018-05-10'}
        try: Dep.create({**dv, 'relationship': 'child', 'is_registered': True})
        except Exception: Dep.create(dv)
        log("✓ người phụ thuộc Hoa")
except Exception as e: log("dep Hoa:", e)
try: mk_leave(hoa, '2026-06-12', '2026-06-13', 'Việc gia đình'); log("✓ nghỉ phép Hoa")
except Exception as e: log("leave Hoa:", e)
try: mk_appraisal(hoa); log("✓ đánh giá KPI/OKR Hoa")
except Exception as e: log("appraisal Hoa:", e)

# Minh + Bình — phiếu lương + chấm công (cho danh sách có người)
for e2, w, p, a, o, n in [(minh, 16000000, 0, 2500000, 0, 0), (mgr, 11000000, 0, 1500000, 6, 0)]:
    try: mk_payslip(e2, w, piece=p, allow_tax=a, ot=o, night=n)
    except Exception as ex: log("payslip", e2.name, ex)
    try: mk_attendance(e2, ot=o)
    except Exception as ex: log("att", e2.name, ex)
log("✓ phiếu lương + chấm công cho Minh & Bình")

# ── Nhà máy: phòng ban kiểu xưởng may + 20 nhân viên ─────
DEPTS = {
    'gd': 'Ban Giám đốc', 'hr': 'Phòng Nhân sự', 'kt': 'Phòng Kế toán',
    'cat': 'Xưởng A · Tổ Cắt', 'may1': 'Xưởng A · Chuyền may 1', 'may2': 'Xưởng A · Chuyền may 2',
    'may4': 'Xưởng B · Chuyền may 4', 'ht': 'Tổ Hoàn thiện (là · đóng gói)',
    'qc': 'Tổ QC · Kiểm soát chất lượng', 'cd': 'Tổ Cơ điện · Bảo trì', 'kho': 'Kho Nguyên phụ liệu',
}
dmap = {k: ensure('hr.department', [('name', '=', v)], {'name': v}) for k, v in DEPTS.items()}
dmap['may3'] = dept_xuong  # Chuyền may 3 · Xưởng A (đã có)

STAFF = [
    # (tên, sex, chức danh, dept_key, lương, ca_đêm)
    ('Phạm Thị Lan', 'female', 'Công nhân may', 'may1', 6200000, False),
    ('Hoàng Văn Tú', 'male', 'Công nhân cắt', 'cat', 6800000, False),
    ('Trần Thị Mai', 'female', 'Nhân viên QC', 'qc', 7500000, False),
    ('Lê Thị Hồng', 'female', 'Công nhân may', 'may1', 6300000, False),
    ('Nguyễn Văn Dũng', 'male', 'Kỹ thuật viên cơ điện', 'cd', 9500000, True),
    ('Vũ Thị Thu', 'female', 'Công nhân may', 'may2', 6100000, False),
    ('Đặng Văn Hải', 'male', 'Thủ kho', 'kho', 8000000, False),
    ('Bùi Thị Nga', 'female', 'Công nhân hoàn thiện', 'ht', 6000000, False),
    ('Phan Thị Hà', 'female', 'Công nhân may', 'may2', 6400000, True),
    ('Đỗ Văn Nam', 'male', 'Tổ phó chuyền may', 'may4', 9000000, False),
    ('Ngô Thị Yến', 'female', 'Công nhân may', 'may4', 6250000, False),
    ('Dương Văn Khoa', 'male', 'Nhân viên QC', 'qc', 7300000, False),
    ('Lý Thị Bích', 'female', 'Công nhân hoàn thiện', 'ht', 6050000, False),
    ('Trịnh Văn Long', 'male', 'Công nhân cắt', 'cat', 6900000, False),
    ('Hồ Thị Diệu', 'female', 'Công nhân may', 'may3', 6350000, True),
    ('Cao Văn Sơn', 'male', 'Nhân viên kế toán', 'kt', 13000000, False),
    ('Đinh Thị Hằng', 'female', 'Chuyên viên nhân sự', 'hr', 12000000, False),
    ('Mai Văn Phúc', 'male', 'Công nhân may', 'may1', 6150000, False),
    ('Tô Thị Loan', 'female', 'Công nhân may', 'may2', 6200000, False),
    ('Đoàn Văn Thành', 'male', 'Giám đốc sản xuất', 'gd', 22000000, False),
]
nnv = 0
for i, (name, sex, job, dk, wage, night_shift) in enumerate(STAFF, 1):
    try:
        e = mk_emp(name, 'NV%04d' % i, 'NV-%04d' % i, sex, job, dmap[dk], wage, '09%08d' % (10000000 + i))
        ot = [0, 6, 12, 18][i % 4]
        night = 24 if night_shift else 0
        piece = int(wage * 0.4) if ('may' in job.lower() or 'cắt' in job.lower()) else 0
        mk_payslip(e, wage, piece=piece, allow_tax=(1500000 if piece else 2000000), ot=ot, night=night)
        mk_attendance(e, ot=ot, night=night)
        nnv += 1
    except Exception as ex:
        log("NV", name, ex)
log("✓ +%d nhân viên nhà máy (phiếu lương + chấm công)" % nnv)

# ── Sinh thêm công nhân may cho đủ 50 NV ─────────────────
SUR = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Phan', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô',
       'Dương', 'Lý', 'Đinh', 'Mai', 'Tô', 'Trịnh', 'Cao', 'Đoàn', 'Vương', 'Hà', 'Tạ', 'Chu',
       'Kiều', 'Thái', 'Lâm', 'Trương', 'Lưu', 'Đào']
GF = ['Hoa', 'Lan', 'Mai', 'Hồng', 'Thu', 'Nga', 'Hà', 'Yến', 'Bích', 'Diệu', 'Hằng', 'Loan', 'Thảo',
      'Trang', 'Linh', 'Vân', 'Huệ', 'Nhung', 'Oanh', 'Phượng', 'Quỳnh', 'Tâm', 'Uyên', 'Xuân', 'Kim', 'Như', 'Thúy']
GM = ['Tú', 'Dũng', 'Hải', 'Nam', 'Khoa', 'Long', 'Sơn', 'Phúc', 'Thành', 'Cường', 'Đạt', 'Hùng', 'Khánh',
      'Lâm', 'Phong', 'Quân', 'Sang', 'Tài', 'Trung', 'Vinh', 'An', 'Bảo', 'Đức', 'Kiên', 'Lộc', 'Mạnh', 'Nghĩa']
MAYS = ['may1', 'may2', 'may3', 'may4']
need = max(0, 50 - HR.search_count([]))
ng = 0
for n in range(need):
    k = len(STAFF) + n + 1
    female = (n % 3 != 0)  # ~2/3 nữ (đặc thù ngành may)
    giv_list = GF if female else GM
    name = '%s %s %s' % (SUR[n % len(SUR)], 'Thị' if female else 'Văn', giv_list[n % len(giv_list)])
    wage = 6000000 + (n % 6) * 100000
    try:
        e = mk_emp(name, 'NV%04d' % k, 'NV-%04d' % k, 'female' if female else 'male',
                   'Công nhân may', dmap[MAYS[n % 4]], wage, '09%08d' % (10000000 + k))
        ot = [0, 6, 12][n % 3]
        mk_payslip(e, wage, piece=int(wage * 0.4), allow_tax=1500000, ot=ot, night=0)
        mk_attendance(e, ot=ot)
        ng += 1
    except Exception as ex:
        log("genNV", name, ex)
log("✓ +%d công nhân (tổng %d NV)" % (ng, HR.search_count([])))

# Đăng nhập demo CÔNG KHAI: login=demo / password=demo (khớp landing sapiones.com)
try:
    admin = env.ref('base.user_admin', raise_if_not_found=False)
    if admin:
        admin.write({'login': 'demo', 'password': 'demo'})
        log("✓ đăng nhập demo: demo / demo")
except Exception as e:
    log("set login demo:", e)

env.cr.commit()
print("\n✅ SEED DEMO XONG — %d nhân viên; đăng nhập demo/demo; có phiếu lương/chấm công/nghỉ phép/công việc/đánh giá."
      % HR.search_count([]))

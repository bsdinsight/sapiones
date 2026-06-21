# -*- coding: utf-8 -*-
"""Seed dữ liệu HR cho nhân viên demo (nhà máy may): Ngày vào làm, ĐT công ty,
Chức vụ (job_id + job_title), Quản lý (parent_id) + manager phòng ban + cây tổ chức.

Chạy:  odoo shell -d <db> --no-http  < seed_employee_hr.py
Idempotent: chỉ điền field đang TRỐNG → chạy lại an toàn, không ghi đè dữ liệu thật.
"""
import random
from datetime import date, timedelta

random.seed(42)  # ổn định: chạy lại cho cùng kết quả

Emp = env['hr.employee'].sudo()
Job = env['hr.job'].sudo()
Dept = env['hr.department'].sudo()

# Chức vụ theo phòng ban: (keyword trong tên dept, chức vụ nhân viên, chức vụ quản lý)
ROLE_MAP = [
    ('giám đốc',    'Trợ lý giám đốc',        'Tổng Giám đốc'),
    ('chuyền may',  'Công nhân may',          'Chuyền trưởng'),
    ('tổ cắt',      'Công nhân cắt',          'Tổ trưởng tổ cắt'),
    ('hoàn thiện',  'Công nhân hoàn thiện',   'Tổ trưởng hoàn thiện'),
    ('qc',          'Nhân viên QC',           'Tổ trưởng QC'),
    ('kho',         'Nhân viên kho',          'Thủ kho'),
    ('cơ điện',     'KTV cơ điện',            'Tổ trưởng cơ điện'),
    ('kế toán',     'Kế toán viên',           'Kế toán trưởng'),
    ('kinh doanh',  'Nhân viên kinh doanh',   'Trưởng phòng kinh doanh'),
    ('nhân sự',     'Chuyên viên nhân sự',    'Trưởng phòng nhân sự'),
    ('quản trị',    'Chuyên viên hành chính', 'Trưởng phòng hành chính'),
]
DEFAULT_STAFF, DEFAULT_LEAD = 'Nhân viên', 'Trưởng nhóm'


def roles_for(dept_name):
    n = (dept_name or '').lower()
    for kw, staff, lead in ROLE_MAP:
        if kw in n:
            return staff, lead
    return DEFAULT_STAFF, DEFAULT_LEAD


_job_cache = {}
def job(title):
    if title not in _job_cache:
        j = Job.search([('name', '=', title)], limit=1) or Job.create({'name': title})
        _job_cache[title] = j
    return _job_cache[title]


def rand_phone():
    head = random.choice(['090', '091', '093', '098', '032', '035', '038', '070', '077', '081'])
    return '%s %s %s' % (head, random.randint(100, 999), random.randint(1000, 9999))


def rand_join_date(is_lead):
    # quản lý vào sớm hơn (2-7 năm), nhân viên 1 tháng - 4 năm
    days = random.randint(730, 2555) if is_lead else random.randint(30, 1460)
    return date.today() - timedelta(days=days)


updated = 0
top_manager = None  # Giám đốc — các trưởng phòng report lên

for dept in Dept.search([]):
    emps = Emp.search([('department_id', '=', dept.id)])
    # bỏ qua "Khách tham quan" / khách: không gán chức vụ, quản lý
    emps = emps.filtered(lambda e: 'khách' not in (e.name or '').lower())
    if not emps:
        continue

    staff_title, lead_title = roles_for(dept.name)
    lead = dept.manager_id if (dept.manager_id and dept.manager_id in emps) else emps[0]

    for e in emps:
        is_lead = e == lead
        vals = {}
        if not e.job_id:
            vals['job_id'] = job(lead_title if is_lead else staff_title).id
        if not e.job_title:
            vals['job_title'] = lead_title if is_lead else staff_title
        if not e.work_phone:
            vals['work_phone'] = rand_phone()
        if not e.mobile_phone:
            vals['mobile_phone'] = rand_phone()
        if not e.date_join:
            vals['date_join'] = rand_join_date(is_lead)
        if not e.parent_id and not is_lead:
            vals['parent_id'] = lead.id
        if vals:
            e.write(vals)
            updated += 1

    if not dept.manager_id:
        dept.manager_id = lead.id
    if 'giám đốc' in (dept.name or '').lower():
        top_manager = lead

# Trưởng phòng/tổ trưởng report lên Giám đốc
if top_manager:
    for dept in Dept.search([]):
        lead = dept.manager_id
        if lead and lead != top_manager and not lead.parent_id:
            lead.parent_id = top_manager.id
            updated += 1

env.cr.commit()
print('SEED_OK: cập nhật', updated, 'nhân viên |', len(_job_cache), 'chức vụ')
for e in Emp.search([], limit=4):
    print('  -', e.name, '|', e.job_title or '', '|', e.work_phone or '',
          '|', (e.date_join and e.date_join.strftime('%d/%m/%Y')) or '',
          '| QL:', e.parent_id.name or '—')

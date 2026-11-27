# -*- coding: utf-8 -*-
"""SEED DEMO — Thang bậc lương (hệ số) của công ty may mẫu + gắn bậc cho nhân viên.

Lương cơ bản = hệ số × 5.000.000 đ (mức làm cơ sở xếp thang của CÔNG TY MẪU — khớp lương
cơ bản đã nạp trên hồ sơ: công nhân 6,0–6,5 tr, trưởng phòng 12–16 tr, TGĐ 22 tr).
27 bậc / 6 nhóm. Tổ trưởng, chuyền trưởng xếp theo thang công nhân (hưởng thêm phụ cấp trách nhiệm).
Mỗi nhân viên được gắn bậc trong nhóm của mình có mức lương gần nhất với lương cơ bản hiện tại.

Chỉ là DỮ LIỆU MẪU. Chạy lại: bỏ qua nếu đã có bậc lương.
Run (VPS): docker run ... odoo shell -d demo --no-http < demo-data/packs/seed_salary_grade_demo.py
"""
BASE = 5_000_000
Grade = env['sapiones.salary.grade'].sudo()
Emp = env['hr.employee'].sudo().with_context(tracking_disable=True, mail_notrack=True)

if Grade.with_context(active_test=False).search_count([]):
    print('Đã có bậc lương — bỏ qua.')
    raise SystemExit

# (mã, tên, nhóm, hệ số, điều kiện xếp bậc)
GRADES = [
    ('CN1', 'Công nhân bậc 1', 'worker', 1.20, 'Hết thử việc, đang làm quen định mức chuyền'),
    ('CN2', 'Công nhân bậc 2', 'worker', 1.24, 'Đạt định mức ổn định từ 6 tháng'),
    ('CN3', 'Công nhân bậc 3', 'worker', 1.28, 'Thành thạo 2–3 công đoạn'),
    ('CN4', 'Công nhân bậc 4', 'worker', 1.32, 'Thành thạo từ 4 công đoạn, KPI từ Khá hai kỳ liền'),
    ('CN5', 'Công nhân bậc 5', 'worker', 1.40, 'May được công đoạn khó (tra cổ, tra tay, mí nẹp), kèm cặp người mới'),
    ('CN6', 'Công nhân bậc 6', 'worker', 1.50, 'Thợ đa năng, đứng được máy chuyên dùng'),
    ('CN7', 'Công nhân bậc 7', 'worker', 1.60, 'Thợ bậc cao / thợ may mẫu'),
    ('KT1', 'Kỹ thuật viên bậc 1', 'technician', 1.50, 'Thợ cơ điện, kỹ thuật chuyền mới'),
    ('KT2', 'Kỹ thuật viên bậc 2', 'technician', 1.60, 'Sửa được máy may 1 kim, 2 kim'),
    ('KT3', 'Kỹ thuật viên bậc 3', 'technician', 1.75, 'Sửa máy chuyên dùng (vắt sổ, trần đè, thùa khuy)'),
    ('KT4', 'Kỹ thuật viên bậc 4', 'technician', 1.90, 'Vận hành nồi hơi, hệ thống điện; phụ trách tổ'),
    ('KT5', 'Kỹ thuật viên bậc 5', 'technician', 2.10, 'Kỹ thuật trưởng xưởng'),
    ('NV1', 'Nhân viên bậc 1', 'staff', 1.40, 'Nhân viên văn phòng, kho, QC mới'),
    ('NV2', 'Nhân viên bậc 2', 'staff', 1.50, 'Từ 1 năm kinh nghiệm'),
    ('NV3', 'Nhân viên bậc 3', 'staff', 1.60, 'Từ 2 năm, làm độc lập'),
    ('NV4', 'Nhân viên bậc 4', 'staff', 1.75, 'Từ 3 năm, kiêm nhiệm hoặc phụ trách nhóm nhỏ'),
    ('NV5', 'Nhân viên bậc 5', 'staff', 1.90, 'Nhân viên chính'),
    ('CV1', 'Chuyên viên bậc 1', 'specialist', 2.00, 'Tốt nghiệp đại học, từ 3 năm chuyên môn'),
    ('CV2', 'Chuyên viên bậc 2', 'specialist', 2.20, 'Chuyên viên phụ trách mảng'),
    ('CV3', 'Chuyên viên bậc 3', 'specialist', 2.40, 'Chuyên viên chính'),
    ('CV4', 'Chuyên viên bậc 4', 'specialist', 2.60, 'Chuyên viên cao cấp'),
    ('QL1', 'Quản lý bậc 1', 'manager', 2.40, 'Phó phòng; trưởng phòng dưới 2 năm'),
    ('QL2', 'Quản lý bậc 2', 'manager', 2.60, 'Trưởng phòng, kế toán trưởng'),
    ('QL3', 'Quản lý bậc 3', 'manager', 2.80, 'Quản đốc xưởng; trưởng phòng từ 3 năm'),
    ('QL4', 'Quản lý bậc 4', 'manager', 3.20, 'Trưởng khối; trưởng phòng kinh doanh có chỉ tiêu doanh số'),
    ('LD1', 'Phó Tổng Giám đốc', 'director', 3.80, 'Lãnh đạo công ty'),
    ('LD2', 'Tổng Giám đốc', 'director', 4.40, 'Lãnh đạo công ty'),
]
grades = {}
seq = {}
for code, name, cat, co, cond in GRADES:
    seq[cat] = seq.get(cat, len(seq) * 10 + 10) + 1
    grades[code] = Grade.create({
        'code': code, 'name': name, 'category': cat, 'coefficient': co, 'sequence': seq[cat],
        'note': '%s — lương cơ bản %s đ' % (cond, '{:,.0f}'.format(co * BASE).replace(',', '.'))})


def category(e):
    j = (e.job_id.name or e.job_title or '').lower()
    if 'giám đốc' in j or 'chief executive' in j:
        return 'director'
    if 'trưởng phòng' in j or 'kế toán trưởng' in j:
        return 'manager'
    if 'cơ điện' in j:
        return 'technician'
    if any(k in j for k in ('công nhân', 'chuyền trưởng', 'tổ trưởng')) and 'qc' not in j:
        return 'worker'
    return 'staff'


assigned = {}
for e in Emp.search([('base_wage', '>', 0)]):
    cat = category(e)
    cand = [g for g in grades.values() if g.category == cat]
    g = min(cand, key=lambda g: (abs(g.coefficient * BASE - e.base_wage), g.coefficient))
    if cat == 'director' and 'phó' not in (e.job_id.name or e.job_title or '').lower():
        g = grades['LD2']
    e.salary_grade_id = g
    assigned[g.code] = assigned.get(g.code, 0) + 1

env.cr.commit()
print('Bậc lương: %d' % len(grades))
print('Gắn bậc: %d nhân viên' % sum(assigned.values()), dict(sorted(assigned.items())))

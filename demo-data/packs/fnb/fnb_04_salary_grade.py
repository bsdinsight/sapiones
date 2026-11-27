# -*- coding: utf-8 -*-
"""SEED DEMO F&B — Thang bậc lương (hệ số) của chuỗi cà phê mẫu + gắn bậc cho nhân viên toàn thời gian.

Lương cơ bản = hệ số × 5.000.000 đ (mức làm cơ sở xếp thang của CÔNG TY MẪU — khớp lương đã nạp ở
fnb_01_base.py). Nhân viên bán thời gian hưởng lương theo giờ nên KHÔNG xếp bậc.
Chỉ là DỮ LIỆU MẪU. Chạy lại: bỏ qua nếu đã có bậc lương.
"""
BASE = 5_000_000
Grade = env['sapiones.salary.grade'].sudo()
Emp = env['hr.employee'].sudo().with_context(tracking_disable=True, mail_notrack=True)

if Grade.with_context(active_test=False).search_count([]):
    print('Đã có bậc lương — bỏ qua.')
    raise SystemExit

# (mã, tên, nhóm, hệ số, điều kiện xếp bậc)
GRADES = [
    ('CH1', 'Nhân viên cửa hàng bậc 1', 'staff', 1.40, 'Hết thử việc, làm được một vị trí (phục vụ hoặc thu ngân)'),
    ('CH2', 'Nhân viên cửa hàng bậc 2', 'staff', 1.44, 'Pha chế đủ menu cơ bản, đạt kiểm tra công thức'),
    ('CH3', 'Nhân viên cửa hàng bậc 3', 'staff', 1.50, 'Làm được mọi vị trí trong ca, từ 1 năm'),
    ('CH4', 'Nhân viên cửa hàng bậc 4', 'staff', 1.56, 'Barista chính, kèm cặp người mới'),
    ('BP1', 'Bếp bậc 1', 'technician', 1.40, 'Phụ bếp mới: sơ chế, vệ sinh khu bếp'),
    ('BP2', 'Bếp bậc 2', 'technician', 1.44, 'Phụ bếp: chế biến món cơ bản theo định lượng'),
    ('BP3', 'Bếp bậc 3', 'technician', 1.80, 'Đứng bếp một khu, kiểm soát hao hụt'),
    ('BP4', 'Bếp bậc 4', 'technician', 2.30, 'Bếp chính: lên món mới, kèm cặp phụ bếp'),
    ('BP5', 'Bếp bậc 5', 'technician', 2.40, 'Bếp chính bếp trung tâm, phụ trách một dây chuyền'),
    ('VP1', 'Chuyên viên bậc 1', 'specialist', 1.56, 'Nhân viên kho, nhân viên hỗ trợ mới'),
    ('VP2', 'Chuyên viên bậc 2', 'specialist', 1.60, 'Nhân viên kho từ 1 năm'),
    ('VP3', 'Chuyên viên bậc 3', 'specialist', 2.10, 'Chuyên viên mới: QA, mua hàng, kế toán'),
    ('VP4', 'Chuyên viên bậc 4', 'specialist', 2.20, 'Chuyên viên làm độc lập'),
    ('VP5', 'Chuyên viên bậc 5', 'specialist', 2.30, 'Chuyên viên phụ trách mảng'),
    ('VP6', 'Chuyên viên bậc 6', 'specialist', 2.40, 'Chuyên viên chính'),
    ('VP7', 'Chuyên viên bậc 7', 'specialist', 2.60, 'Chuyên viên cao cấp: tuyển dụng, đào tạo, marketing'),
    ('VP8', 'Chuyên viên bậc 8', 'specialist', 2.70, 'Chuyên viên cao cấp C&B'),
    ('QL1', 'Quản lý bậc 1', 'manager', 1.90, 'Ca trưởng mới'),
    ('QL2', 'Quản lý bậc 2', 'manager', 2.00, 'Ca trưởng từ 1 năm, mở/đóng ca độc lập'),
    ('QL3', 'Quản lý bậc 3', 'manager', 3.00, 'Cửa hàng trưởng'),
    ('QL4', 'Quản lý bậc 4', 'manager', 3.20, 'Cửa hàng trưởng cửa hàng lớn hoặc từ 2 năm'),
    ('QL5', 'Quản lý bậc 5', 'manager', 3.60, 'Trưởng nhóm khối văn phòng'),
    ('QL6', 'Quản lý bậc 6', 'manager', 4.00, 'Trưởng phòng, bếp trưởng'),
    ('QL7', 'Quản lý bậc 7', 'manager', 4.40, 'Trưởng phòng có chỉ tiêu toàn chuỗi'),
    ('QL8', 'Quản lý bậc 8', 'manager', 4.80, 'Quản lý vùng, kế toán trưởng'),
    ('QL9', 'Quản lý bậc 9', 'manager', 5.00, 'Quản lý vùng nhiều cửa hàng'),
    ('LD1', 'Giám đốc khối', 'director', 7.00, 'Lãnh đạo công ty'),
    ('LD2', 'Tổng Giám đốc', 'director', 9.00, 'Lãnh đạo công ty'),
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
    if 'giám đốc' in j:
        return 'director'
    if any(k in j for k in ('trưởng', 'quản lý', 'ca trưởng')):
        return 'manager'
    if 'bếp' in j:
        return 'technician'
    if any(k in j for k in ('barista', 'phục vụ', 'thu ngân')):
        return 'staff'
    return 'specialist'


assigned = {}
for e in Emp.search([('base_wage', '>', 0)]):
    if e.resource_calendar_id.hours_per_day and e.resource_calendar_id.hours_per_day < 8:
        continue  # bán thời gian: lương theo giờ, không xếp bậc
    cat = category(e)
    cand = [g for g in grades.values() if g.category == cat]
    g = min(cand, key=lambda g: (abs(g.coefficient * BASE - e.base_wage), g.coefficient))
    e.salary_grade_id = g
    assigned[g.code] = assigned.get(g.code, 0) + 1

env.cr.commit()
print('Bậc lương: %d' % len(grades))
print('Gắn bậc: %d nhân viên' % sum(assigned.values()), dict(sorted(assigned.items())))

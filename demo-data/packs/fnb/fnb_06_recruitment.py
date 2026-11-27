# -*- coding: utf-8 -*-
"""SEED DEMO F&B — Tuyển dụng: yêu cầu tuyển dụng theo cửa hàng / khối văn phòng + ứng viên các bước.

Chuỗi cà phê tuyển nhiều bán thời gian (sinh viên) quanh mùa cao điểm; nguồn chủ yếu mạng xã hội,
giới thiệu nội bộ, mã QR tại quầy (ghi nguồn "Khác"). Tên ứng viên là dữ liệu minh họa.
Chạy lại: bỏ qua nếu đã có yêu cầu tuyển dụng.
"""
import random
from datetime import timedelta

from odoo import fields

rnd = random.Random(20261131)
today = fields.Date.today()
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True)
Req = env['sapiones.recruitment.requisition'].sudo().with_context(**ctx)
Cand = env['sapiones.candidate'].sudo().with_context(**ctx)
Eval = env['sapiones.interview.evaluation'].sudo().with_context(**ctx)
Dept = env['hr.department'].sudo()
Emp = env['hr.employee'].sudo()

if Req.search_count([]):
    print('Đã có yêu cầu tuyển dụng — bỏ qua.')
    raise SystemExit


def S(xid):
    return env.ref('sapiones_recruitment_vn.' + xid)


def D(name):
    return Dept.search([('name', '=', name)], limit=1)


# (vị trí, phòng ban, số lượng, lương min, lương max, lý do, trạng thái, ngày yêu cầu cách đây)
PT = (3_000_000, 3_600_000)
REQS = [
    ('Barista bán thời gian', 'Cửa hàng Quận 1', 3, *PT, 'Bổ sung ca tối cao điểm Tết', 'approved', 6),
    ('Phục vụ bán thời gian', 'Cửa hàng Quận 1', 2, *PT, 'Bổ sung ca cuối tuần', 'approved', 6),
    ('Barista bán thời gian', 'Cửa hàng Quận 3', 2, *PT, 'Thay nhân viên nghỉ việc', 'approved', 12),
    ('Thu ngân bán thời gian', 'Cửa hàng Bình Thạnh', 2, *PT, 'Bổ sung ca sáng', 'approved', 9),
    ('Barista', 'Cửa hàng Bình Thạnh', 1, 7_000_000, 8_000_000, 'Thay nhân viên chuyển cửa hàng', 'approved', 15),
    ('Phục vụ bán thời gian', 'Cửa hàng Phú Nhuận', 3, *PT, 'Bổ sung ca tối cao điểm Tết', 'approved', 4),
    ('Ca trưởng', 'Cửa hàng Phú Nhuận', 1, 9_000_000, 10_500_000, 'Ca trưởng cũ lên cửa hàng trưởng', 'approved', 20),
    ('Barista bán thời gian', 'Cửa hàng Thủ Đức', 3, *PT, 'Gần trường đại học, mở thêm ca tối', 'approved', 8),
    ('Phụ bếp', 'Cửa hàng Thủ Đức', 1, 6_800_000, 7_500_000, 'Mở thêm món ăn nhẹ', 'submitted', 2),
    ('Barista bán thời gian', 'Cửa hàng Hoàn Kiếm', 2, *PT, 'Mùa du lịch cuối năm', 'approved', 10),
    ('Phục vụ bán thời gian', 'Cửa hàng Cầu Giấy', 2, *PT, 'Thay sinh viên nghỉ thi', 'approved', 7),
    ('Cửa hàng trưởng', 'Cửa hàng Đống Đa', 1, 15_000_000, 18_000_000, 'Chuẩn bị mở cửa hàng mới khu Đống Đa 2', 'approved', 25),
    ('Barista', 'Cửa hàng Đống Đa', 2, 7_000_000, 8_000_000, 'Chuẩn bị mở cửa hàng mới', 'approved', 25),
    ('Thu ngân bán thời gian', 'Cửa hàng Hoàn Kiếm', 1, *PT, 'Bổ sung ca sáng', 'draft', 1),
    ('Bếp chính', 'Bếp trung tâm', 1, 11_000_000, 13_000_000, 'Tăng sản lượng bánh cho 8 cửa hàng', 'approved', 18),
    ('Phụ bếp', 'Bếp trung tâm', 2, 6_800_000, 7_500_000, 'Tăng ca sản xuất sáng sớm', 'approved', 14),
    ('Nhân viên kho', 'Mua hàng & Kho', 1, 7_500_000, 8_500_000, 'Thay nhân viên nghỉ việc', 'closed', 60),
    ('Nhân viên QA', 'QA An toàn thực phẩm', 1, 10_000_000, 12_000_000, 'Tăng tần suất kiểm tra cửa hàng', 'approved', 21),
    ('Chuyên viên nội dung', 'Marketing', 1, 11_000_000, 13_000_000, 'Chạy chương trình thành viên', 'closed', 75),
    ('Chuyên viên tuyển dụng', 'Nhân sự & Đào tạo', 1, 12_000_000, 14_000_000, 'Tuyển cao điểm Tết', 'approved', 30),
    ('Kế toán viên', 'Kế toán', 1, 11_000_000, 12_500_000, 'Đối soát doanh thu cửa hàng', 'rejected', 40),
    ('Quản lý vùng', 'Vùng Hà Nội', 1, 22_000_000, 26_000_000, 'Mở rộng lên 5 cửa hàng Hà Nội', 'submitted', 3),
]
demo_user = env['res.users'].sudo().search([('login', '=', 'demo')], limit=1)  # người tạo yêu cầu = tài khoản demo
reqs = []
for title, dname, hc, smin, smax, reason, state, ago in REQS:
    d = D(dname)
    reqs.append(Req.create({'job_title': title, 'department_id': d.id, 'headcount': hc,
                            'salary_min': smin, 'salary_max': smax, 'reason': reason,
                            'requested_by': demo_user.id,
                            'date_request': today - timedelta(days=ago),
                            'date_needed': today + timedelta(days=rnd.choice((7, 14, 21, 30))),
                            'state': state}))

F = ['Nguyễn Ngọc Anh', 'Trần Thu Trang', 'Lê Khánh Linh', 'Phạm Bảo Vy', 'Hoàng Gia Hân', 'Võ Minh Thư',
     'Đặng Thanh Ngân', 'Bùi Phương Thảo', 'Đỗ Ngọc My', 'Hồ Thanh Uyên', 'Ngô Bảo Ngọc', 'Dương Khánh Vy',
     'Lý Minh Châu', 'Mai Thu Hà', 'Tô Ngọc Hân', 'Trịnh Thanh Tâm', 'Cao Thùy Dương', 'Lâm Bảo Trân']
M = ['Nguyễn Minh Khoa', 'Trần Quốc Huy', 'Lê Đức Phúc', 'Phạm Gia Bảo', 'Hoàng Tuấn Kiệt', 'Vũ Thành Đạt',
     'Đặng Minh Khang', 'Bùi Quốc Vinh', 'Đỗ Hoàng Long', 'Hồ Đức Duy', 'Ngô Gia Huy', 'Dương Thành Nhân',
     'Lý Hoàng Nam', 'Mai Tuấn Tú']
names = F + M
rnd.shuffle(names)
SRC = [('social', 40), ('referral', 20), ('other', 15), ('jobboard', 15), ('website', 10)]
STAGE_BY_STATE = {'approved': [('stage_new', 30), ('stage_screening', 25), ('stage_interview', 25),
                               ('stage_offer', 10), ('stage_hired', 5), ('stage_refused', 5)],
                  'closed': [('stage_hired', 60), ('stage_refused', 40)]}


def pick(w):
    items, ws = zip(*w)
    return rnd.choices(items, weights=ws)[0]


COMMENTS = {'hire': ['Nhanh nhẹn, giao tiếp tốt, nhận được ca tối và cuối tuần.',
                     'Đã có kinh nghiệm pha chế, làm thử đạt.',
                     'Thái độ phục vụ tốt, phù hợp văn hoá cửa hàng.'],
            'hold': ['Lịch học chưa ổn định, chờ xác nhận lịch ca.', 'Cần làm thử thêm một ca.'],
            'reject': ['Không nhận được ca cuối tuần.', 'Chưa phù hợp yêu cầu giờ cao điểm.']}
n = 0
pool = [r for r in reqs if r.state in ('approved', 'closed')]
for i, nm in enumerate(names):
    r = pool[i % len(pool)]
    st = pick(STAGE_BY_STATE[r.state])
    pt = 'bán thời gian' in r.job_title
    exp = (rnd.choice((28000, 30000, 32000)) * 4 * 26) if pt else int(((r.salary_min + r.salary_max) / 2) // 100000 * 100000)
    c = Cand.create({'name': nm, 'requisition_id': r.id, 'job_title': r.job_title, 'department_id': r.department_id.id,
                     'stage_id': S(st).id, 'source': pick(SRC), 'priority': rnd.choice('0012'),
                     'expected_salary': exp,
                     'proposed_salary': exp if st in ('stage_offer', 'stage_hired') else 0,
                     'email': 'ungvien.fnb%02d@example.com' % (i + 1),
                     'phone': '09%d %03d %04d' % (rnd.randint(0, 9), rnd.randint(100, 999), rnd.randint(1000, 9999))})
    if st in ('stage_interview', 'stage_offer', 'stage_hired', 'stage_refused'):
        rec = 'reject' if st == 'stage_refused' else ('hire' if st != 'stage_interview' else pick([('hire', 60), ('hold', 40)]))
        base = {'hire': 8, 'hold': 6.5, 'reject': 5}[rec]
        Eval.create({'candidate_id': c.id, 'interviewer_id': (r.department_id.manager_id.user_id.id or False),
                     'date': today - timedelta(days=rnd.randint(1, 10)),
                     'score_technical': round(base + rnd.uniform(-1, 1), 1),
                     'score_communication': round(base + rnd.uniform(-1, 1.5), 1),
                     'score_attitude': round(base + rnd.uniform(-0.5, 1.5), 1),
                     'score_fit': round(base + rnd.uniform(-1, 1), 1),
                     'recommendation': rec, 'comment': rnd.choice(COMMENTS[rec])})
    n += 1

env.cr.commit()
print('Yêu cầu tuyển dụng:', Req.search_count([]), dict((s, Req.search_count([('state', '=', s)])) for s in ('draft', 'submitted', 'approved', 'rejected', 'closed')))
print('Ứng viên:', Cand.search_count([]), [(str(k), c) for k, c in Cand._read_group([], ['stage_id'], ['__count'])])
print('Phiếu phỏng vấn:', Eval.search_count([]))

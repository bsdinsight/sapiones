# -*- coding: utf-8 -*-
"""SEED DEMO — Đánh giá hiệu suất (KPI tháng + OKR) cho demo (công ty may mặc).

- Đợt KPI hằng tháng 01/<năm trước> → tháng hiện tại. Các tháng đã qua: Hoàn tất;
  tháng hiện tại: Đang đánh giá, phiếu rải đủ trạng thái Nháp / NV tự ĐG / QL ĐG / Hoàn tất.
- Mỗi phiếu có bộ chỉ tiêu theo vị trí (công nhân may, cắt, hoàn thiện, chuyền trưởng,
  QC, kho, cơ điện, kế toán, nhân sự, kinh doanh, ban giám đốc, văn phòng).
  Điểm = năng lực riêng của từng người + dao động theo tháng → xếp loại phân bố tự nhiên.
- Người đánh giá = quản lý trực tiếp (parent_id).
- OKR: mục tiêu công ty / phòng ban / cá nhân năm hiện tại (đang theo dõi) + năm trước (đã đóng).
- Không gửi email.

Chỉ là DỮ LIỆU MẪU. Hạt giống cố định. Chạy lại: bỏ qua nếu đã có hơn 5 đợt đánh giá.
Cần sapiones_performance_vn >= 19.0.1.0.1 (phiếu chưa chấm không bị xếp "Chưa đạt").

Run (VPS):
  docker run ... odoo shell -d demo --no-http < demo-data/packs/seed_performance_demo.py
"""
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields

rnd = random.Random(20261127)
today = fields.Date.today()
YEAR = today.year
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True)
Cycle = env['sapiones.appraisal.cycle'].sudo().with_context(**ctx)
Appr = env['sapiones.appraisal'].sudo().with_context(**ctx)
Obj = env['sapiones.objective'].sudo().with_context(**ctx)
Emp = env['hr.employee'].sudo()
mail_before = env['mail.mail'].sudo().search([], order='id desc', limit=1).id or 0

if Cycle.search_count([]) > 5:
    print('Đã seed đánh giá trước đó — bỏ qua.')
    raise SystemExit


def vn(x, nd=1):
    """Số kiểu Việt Nam: 96,2"""
    return ('%.*f' % (nd, x)).replace('.', ',')


# ── Bộ chỉ tiêu theo vị trí ─────────────────────────────
# (tên, trọng số, mục tiêu, hàm sinh kết quả thực tế từ điểm 0–100)
def pct_hi(base):      # càng cao càng tốt, base = mức đạt điểm 90
    return lambda s: vn(base * (0.80 + s / 450)) + '%'


def pct_lo(base):      # càng thấp càng tốt (tỷ lệ lỗi, hao hụt…)
    return lambda s: vn(max(base * (1.9 - s / 100), 0.1)) + '%'


def days(lo):
    return lambda s: '%d/26 công' % min(26, max(lo, round(26 - (100 - s) / 6)))


def count_lo(unit):
    return lambda s: '%d %s' % (max(0, round((100 - s) / 9)), unit)


def okfail(s):
    return 'Đạt' if s >= 70 else 'Chưa đạt (%d lỗi)' % max(1, round((90 - s) / 8))


KPI = {
    'sew': [('Năng suất so với định mức', 40, '≥ 100% định mức', pct_hi(100)),
            ('Tỷ lệ hàng lỗi cá nhân', 25, '≤ 2%', pct_lo(2)),
            ('Chuyên cần', 20, '≥ 25/26 công', days(21)),
            ('Tuân thủ ATLĐ & 5S', 15, 'Không vi phạm', okfail)],
    'cut': [('Năng suất cắt so với kế hoạch', 40, '≥ 100% kế hoạch', pct_hi(100)),
            ('Hao hụt vải', 25, '≤ 1,5%', pct_lo(1.5)),
            ('Chuyên cần', 20, '≥ 25/26 công', days(21)),
            ('Tuân thủ ATLĐ máy cắt', 15, 'Không vi phạm', okfail)],
    'finish': [('Sản lượng là – đóng gói', 40, '≥ 100% kế hoạch', pct_hi(100)),
               ('Sai quy cách đóng gói', 25, '≤ 0,5%', pct_lo(0.5)),
               ('Chuyên cần', 20, '≥ 25/26 công', days(21)),
               ('Tuân thủ 5S khu hoàn thiện', 15, 'Không vi phạm', okfail)],
    'line': [('Đạt kế hoạch sản lượng chuyền', 35, '≥ 100%', pct_hi(100)),
             ('Tỷ lệ lỗi chuyền (end-line)', 25, '≤ 2,5%', pct_lo(2.5)),
             ('Giao hàng đúng hạn', 20, '≥ 97% đơn', pct_hi(97)),
             ('Tỷ lệ nghỉ việc trong tổ', 10, '≤ 3%/tháng', pct_lo(3)),
             ('An toàn lao động', 10, '0 tai nạn', count_lo('sự cố'))],
    'qc': [('Lỗi lọt sang khách hàng', 40, '≤ 0,3%', pct_lo(0.3)),
           ('Kiểm hàng đúng kế hoạch', 30, '100% lô', pct_hi(100)),
           ('Báo cáo chất lượng đúng hạn', 15, 'Trước 9h hằng ngày', okfail),
           ('Chuyên cần', 15, '≥ 25/26 công', days(22))],
    'store': [('Chênh lệch kiểm kê', 35, '≤ 0,2% giá trị', pct_lo(0.2)),
              ('Cấp phát NPL đúng hạn cho chuyền', 35, '≥ 98% phiếu', pct_hi(98)),
              ('Báo cáo nhập – xuất – tồn', 15, 'Đúng hạn ngày 3', okfail),
              ('Tuân thủ PCCC kho', 15, 'Không vi phạm', okfail)],
    'maint': [('Thời gian dừng máy do hỏng', 40, '≤ 2% giờ chạy', pct_lo(2)),
              ('Bảo trì đúng kế hoạch', 35, '100% hạng mục', pct_hi(100)),
              ('An toàn điện', 25, '0 sự cố', count_lo('sự cố'))],
    'acct': [('Báo cáo tài chính / thuế đúng hạn', 40, '100% đúng hạn', okfail),
             ('Sai sót chứng từ', 30, '≤ 3 lỗi/tháng', count_lo('lỗi')),
             ('Công nợ phải thu quá hạn', 30, '≤ 5% doanh thu', pct_lo(5))],
    'hr': [('Tuyển đủ định biên', 35, '≥ 95% định biên', pct_hi(95)),
           ('Tỷ lệ nghỉ việc toàn công ty', 30, '≤ 3%/tháng', pct_lo(3)),
           ('Lương & BHXH đúng hạn', 35, 'Trước ngày 5', okfail)],
    'sales': [('Giá trị đơn hàng ký mới', 45, '≥ 100% kế hoạch', pct_hi(100)),
              ('Giao hàng đúng hạn', 30, '≥ 97% đơn', pct_hi(97)),
              ('Khiếu nại khách hàng', 25, '≤ 1 khiếu nại', count_lo('khiếu nại'))],
    'exec': [('Doanh thu so với kế hoạch', 40, '≥ 100%', pct_hi(100)),
             ('Biên lợi nhuận gộp', 30, '≥ 18%', pct_hi(18)),
             ('Giao hàng đúng hạn toàn nhà máy', 30, '≥ 97% đơn', pct_hi(97))],
    'office': [('Hoàn thành công việc đúng hạn', 40, '≥ 95% đầu việc', pct_hi(95)),
               ('Chất lượng sản phẩm bàn giao', 35, 'Không lỗi nghiêm trọng', okfail),
               ('Hỗ trợ người dùng nội bộ', 25, '≤ 1 ngày phản hồi', okfail)],
}


def kind(e):
    j = (e.job_id.name or e.job_title or '').lower()
    for keys, k in [(('giám đốc', 'chief executive'), 'exec'), (('kế toán',), 'acct'),
                    (('nhân sự',), 'hr'), (('kinh doanh',), 'sales'), (('qc',), 'qc'),
                    (('thủ kho',), 'store'), (('cơ điện',), 'maint'),
                    (('chuyền trưởng', 'tổ trưởng'), 'line'), (('cắt',), 'cut'),
                    (('hoàn thiện',), 'finish'), (('công nhân',), 'sew')]:
        if any(x in j for x in keys):
            return k
    return 'office'


emps = Emp.search([('active', '=', True)], order='id')
ability = {e.id: min(96, max(45, rnd.gauss(76, 9))) for e in emps}
trend = {e.id: rnd.uniform(-0.3, 0.35) for e in emps}   # điểm/tháng: người tiến bộ, người đi xuống
for e in [x for x in emps if (x.job_id.name or '').lower().startswith('công nhân')][5:7]:
    ability[e.id], trend[e.id] = 52, -0.1   # 2 người yếu → có phiếu "Chưa đạt"

SELF_GOOD = ['Hoàn thành tốt định mức, không vi phạm nội quy.',
             'Đã cố gắng giảm lỗi, sẽ tiếp tục cải thiện.',
             'Tháng này đơn hàng gấp, đã tăng ca hỗ trợ chuyền.',
             'Nắm vững công đoạn mới sau đào tạo.']
SELF_WEAK = ['Tháng này nghỉ ốm mấy ngày nên năng suất chưa đạt.',
             'Còn lỗi đường may ở mã hàng mới, cần hướng dẫn thêm.']
MGR = {'excellent': 'Xuất sắc, đề xuất khen thưởng tháng.',
       'good': 'Làm việc tốt, ổn định.',
       'fair': 'Đạt yêu cầu, cần cải thiện tỷ lệ lỗi.',
       'pass': 'Cần kèm cặp thêm, theo dõi tháng sau.',
       'fail': 'Chưa đạt, lập kế hoạch cải thiện 1 tháng.'}

# ── 1. Đợt KPI hằng tháng ───────────────────────────────
start = date(YEAR - 1, 1, 1)
cur_month = today.replace(day=1)
m = start
n_appr = 0
cur_states = {}
while m <= cur_month:
    m_end = m + relativedelta(months=1, days=-1)
    is_cur = (m == cur_month)
    cyc = Cycle.create({'name': 'KPI tháng %02d/%d' % (m.month, m.year),
                        'date_from': m, 'date_to': m_end,
                        'state': 'in_progress' if is_cur else 'done'})
    idx = (m.year - start.year) * 12 + m.month - 1
    season = -3 if m.month in (1, 2) else (-1.5 if m.month in (9, 10) else 0)  # Tết / cao điểm
    pool = [e for e in emps if (e.vn_seniority_date or start) <= m_end - timedelta(days=10)]
    if is_cur:
        rnd.shuffle(pool)
    for i, e in enumerate(pool):
        if is_cur:
            st = 'draft' if i < 8 else 'self' if i < 22 else 'review' if i < 38 else 'done'
        else:
            st = 'done'
        base = ability[e.id] + trend[e.id] * idx + season
        lines = []
        for seq, (name, w, target, res) in enumerate(KPI[kind(e)]):
            s_mgr = round(min(100, max(30, base + rnd.gauss(0, 6))))
            s_self = round(min(100, s_mgr + rnd.uniform(-1, 6)))
            done_self = st in ('review', 'done') or (st == 'self' and seq < 2)
            done_mgr = st == 'done'
            lines.append((0, 0, {'sequence': (seq + 1) * 10, 'name': name, 'weight': w,
                                 'target': target,
                                 'result': res(s_mgr) if done_self else False,
                                 'self_score': s_self if done_self else 0,
                                 'manager_score': s_mgr if done_mgr else 0}))
        a = Appr.create({'cycle_id': cyc.id, 'employee_id': e.id,
                         'manager_id': e.parent_id.id or False,
                         'date_from': m, 'date_to': m_end, 'state': st, 'kpi_ids': lines})
        vals = {}
        if st in ('review', 'done'):
            vals['self_comment'] = rnd.choice(SELF_GOOD if a.self_total >= 75 else SELF_WEAK)
        if st == 'done' and a.rating:
            vals['manager_comment'] = MGR[a.rating]
        if vals:
            a.write(vals)
        if is_cur:
            cur_states[st] = cur_states.get(st, 0) + 1
        n_appr += 1
    m += relativedelta(months=1)
# đợt mẫu cũ của gói demo ("Quý 2/…", chỉ 1 phiếu) lạc giữa các kỳ tháng → gỡ
old = Cycle.search([('name', 'not like', 'KPI tháng')]).filtered(lambda c: len(c.appraisal_ids) <= 1)
print('Gỡ đợt mẫu cũ:', old.mapped('name'))
old.unlink()
# OKR mẫu cũ đã hết kỳ → đóng
Obj.search([('date_to', '<', today), ('state', '=', 'active')]).write({'state': 'closed'})
print('Đợt:', Cycle.search_count([]), '— phiếu mới:', n_appr, '— tháng hiện tại:', cur_states)

# ── 2. OKR ──────────────────────────────────────────────
by_job = {}
for e in emps:
    by_job.setdefault((e.job_id.name or '').lower(), []).append(e)


def who(job_kw):
    for j, lst in by_job.items():
        if job_kw in j:
            return lst[0]
    return Emp


elapsed = (today - date(YEAR, 1, 1)).days / 365.0


def mk_obj(name, level, emp, krs, year=YEAR, closed=False, pace='on'):
    """krs: (tên, chỉ tiêu, mức hoàn thành 0..1 dự kiến cuối kỳ, đơn vị).
    pace (năm hiện tại): 'done' đã đạt sớm · 'on' theo tiến độ năm · 'risk' chậm (< 60 %)."""
    if Obj.search_count([('name', '=', name)]):
        return
    lines = []
    for kr_name, target, reach, uom in krs:
        if closed:
            frac = reach
        elif pace == 'done':
            frac = 1.0
        elif pace == 'risk':
            frac = rnd.uniform(0.3, 0.55)
        else:
            frac = min(1.0, reach * elapsed * rnd.uniform(0.9, 1.08))
        lines.append((0, 0, {'name': kr_name, 'target_value': target,
                             'current_value': round(target * frac, 1), 'uom': uom}))
    Obj.create({'name': name, 'level': level,
                'employee_id': emp.id or False,
                'department_id': (emp.dept_id or emp.department_id).id if emp and level != 'company' else False,
                'date_from': date(year, 1, 1), 'date_to': date(year, 12, 31),
                'state': 'closed' if closed else 'active', 'key_result_ids': lines})


ceo = who('tổng giám đốc')
COMPANY = [
    ('Doanh thu xuất khẩu %d đạt 180 tỷ đồng' % YEAR, [
        ('Doanh thu xuất khẩu', 180, 0.97, 'tỷ đồng'),
        ('Khách hàng mới ký hợp đồng khung', 3, 1.0, 'khách'),
        ('Tỷ trọng đơn FOB', 40, 0.85, '%')]),
    ('Giao hàng đúng hạn từ 97% đơn hàng', [
        ('Đơn giao đúng hạn', 97, 0.99, '%'),
        ('Giảm đơn phải đi máy bay (air) do trễ', 12, 0.75, 'lần cắt giảm')]),
    ('Giảm tỷ lệ lỗi toàn nhà máy xuống 1,5%', [
        ('Chuyền đạt lỗi end-line ≤ 2%', 4, 0.75, 'chuyền'),
        ('Lô hàng đạt AQL lần đầu', 98, 0.97, '%'),
        ('Khiếu nại chất lượng từ khách', 6, 0.5, 'lần cắt giảm')]),
]
for (name, krs), pace in zip(COMPANY, ('on', 'on', 'risk')):
    mk_obj(name, 'company', ceo, krs, pace=pace)

DEPT = [
    ('chuyền trưởng', 'Năng suất chuyền tăng 8% so với năm trước', [
        ('Sản lượng bình quân/người/ngày', 108, 0.97, '% năm trước'),
        ('Công nhân đạt tay nghề bậc 3', 70, 0.9, '%')]),
    ('tổ trưởng tổ cắt', 'Giảm hao hụt vải tổ cắt xuống 1,2%', [
        ('Giảm hao hụt vải (từ 1,8%)', 0.6, 0.8, 'điểm %'),
        ('Áp dụng giác sơ đồ tự động cho mã hàng mới', 100, 1.0, '%')]),
    ('tổ trưởng hoàn thiện', 'Không lô hàng nào sai quy cách đóng gói', [
        ('Lô hàng đóng gói đúng quy cách', 100, 0.99, '%'),
        ('Đào tạo quy cách cho công nhân mới', 100, 1.0, '%')]),
    ('tổ trưởng qc', 'Đạt chứng nhận đánh giá nhà máy của khách hàng', [
        ('Hồ sơ quy trình chất lượng hoàn thiện', 100, 1.0, '%'),
        ('Điểm đánh giá nhà máy (audit)', 85, 0.95, 'điểm')]),
    ('tổ trưởng cơ điện', 'Thời gian dừng máy dưới 2%', [
        ('Máy may được bảo trì định kỳ', 100, 0.95, '%'),
        ('Thời gian dừng máy giảm (từ 3,5%)', 1.5, 0.6, 'điểm %')]),
    ('thủ kho', 'Kho nguyên phụ liệu chính xác 99,8%', [
        ('Độ chính xác tồn kho', 99.8, 1.0, '%'),
        ('Mã NPL có vị trí kệ (định vị)', 100, 0.8, '%')]),
    ('kế toán trưởng', 'Đóng sổ tháng trong 5 ngày làm việc', [
        ('Số tháng đóng sổ đúng hạn', 12, 0.92, 'tháng'),
        ('Công nợ quá hạn dưới 5% doanh thu', 5, 1.0, '%')]),
    ('trưởng phòng nhân sự', 'Giữ chân công nhân — nghỉ việc dưới 3%/tháng', [
        ('Tuyển đủ định biên chuyền may', 120, 0.85, 'người'),
        ('Tỷ lệ nghỉ việc bình quân tháng', 3, 0.5, '% (càng thấp càng tốt)'),
        ('Khảo sát hài lòng người lao động', 80, 0.95, 'điểm')]),
    ('trưởng phòng kinh doanh', 'Mở rộng khách hàng thị trường EU', [
        ('Khách EU ký đơn đầu tiên', 2, 1.0, 'khách'),
        ('Giá trị đơn hàng EU', 25, 0.8, 'tỷ đồng')]),
]
DEPT_PACE = ('on', 'done', 'on', 'done', 'risk', 'on', 'on', 'risk', 'on')
for (kw, name, krs), pace in zip(DEPT, DEPT_PACE):
    mk_obj(name, 'department', who(kw), krs, pace=pace)

# Cá nhân: một số chuyền trưởng / tổ trưởng / công nhân
INDIV = [
    ('Hoàn thành khoá Quản lý sản xuất tinh gọn (Lean)', [
        ('Số buổi học hoàn thành', 10, 1.0, 'buổi'), ('Đề xuất cải tiến được áp dụng', 3, 0.67, 'đề xuất')]),
    ('Đào tạo 2 công nhân đa kỹ năng cho chuyền', [
        ('Công nhân làm được ≥ 3 công đoạn', 2, 1.0, 'người')]),
    ('Đạt tay nghề bậc 4 công nhân may', [
        ('Bài thi tay nghề đạt', 1, 1.0, 'bài'), ('Năng suất bình quân', 110, 0.95, '% định mức')]),
    ('Giảm lỗi đường may cá nhân xuống 1%', [
        ('Giảm tỷ lệ lỗi (từ 2,4%)', 1.4, 0.7, 'điểm %')]),
    ('Học vận hành máy may lập trình', [
        ('Giờ thực hành', 40, 1.0, 'giờ'), ('Mã hàng tự chạy máy', 3, 0.67, 'mã')]),
]
leads = [e for e in emps if kind(e) == 'line'][:6]
workers = [e for e in emps if kind(e) == 'sew']
rnd.shuffle(workers)
targets = [(leads[i % len(leads)], INDIV[i % 2]) for i in range(len(leads))] + \
          [(w, INDIV[2 + i % 3]) for i, w in enumerate(workers[:10])]
for i, (e, (name, krs)) in enumerate(targets):
    mk_obj('%s — %s' % (name, e.name), 'individual', e, krs,
           pace='done' if i % 4 == 1 else 'risk' if i % 5 == 3 else 'on')

# Năm trước: đã đóng
PREV = [
    ('Doanh thu %d đạt 150 tỷ đồng' % (YEAR - 1), 'company', ceo, [
        ('Doanh thu', 150, 1.04, 'tỷ đồng'), ('Khách hàng mới', 2, 1.0, 'khách')]),
    ('Đưa vào vận hành Xưởng B (Chuyền may 4)', 'company', ceo, [
        ('Chuyền chạy ổn định', 1, 1.0, 'chuyền'), ('Tuyển đủ công nhân Xưởng B', 35, 0.9, 'người')]),
    ('Giao hàng đúng hạn 95%% (%d)' % (YEAR - 1), 'company', ceo, [
        ('Đơn giao đúng hạn', 95, 0.98, '%')]),
    ('Số hoá chấm công bằng máy vân tay', 'department', who('trưởng phòng nhân sự'), [
        ('Công nhân đăng ký vân tay', 100, 1.0, '%'), ('Bảng công tự động', 12, 0.75, 'tháng')]),
    ('Giảm tồn kho NPL chậm luân chuyển', 'department', who('thủ kho'), [
        ('Giảm giá trị tồn > 180 ngày', 30, 0.8, '%')]),
    ('Bảo trì phòng ngừa toàn bộ máy may', 'department', who('tổ trưởng cơ điện'), [
        ('Máy có lịch bảo trì', 100, 1.0, '%')]),
]
for name, level, e, krs in PREV:
    mk_obj(name, level, e, krs, year=YEAR - 1, closed=True)

env.flush_all()
junk = env['mail.mail'].sudo().search([('id', '>', mail_before)])
print('Xoá thư đi phát sinh:', len(junk))
junk.unlink()
env.cr.commit()

# ── Tóm tắt ─────────────────────────────────────────────
A = env['sapiones.appraisal'].sudo()
print('Phiếu:', A.search_count([]), '— chưa hoàn tất:', A.search_count([('state', '!=', 'done')]))
print('Xếp loại:', [(str(k), c) for k, c in A._read_group([], ['rating'], ['__count'])])
print('Chỉ tiêu:', env['sapiones.appraisal.kpi'].sudo().search_count([]))
print('OKR:', [(str(k), c) for k, c in Obj._read_group([], ['level'], ['__count'])],
      [(str(k), c) for k, c in Obj._read_group([('state', '=', 'active')], ['status'], ['__count'])])

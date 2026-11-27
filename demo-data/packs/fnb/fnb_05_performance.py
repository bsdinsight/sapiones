# -*- coding: utf-8 -*-
"""SEED DEMO F&B — Đánh giá hiệu suất (KPI tháng + OKR), chuỗi cà phê (bản chỉnh từ seed_performance_demo.py).

- Đợt KPI hằng tháng 01/<năm trước> → tháng hiện tại. Các tháng đã qua: Hoàn tất;
  tháng hiện tại: Đang đánh giá, phiếu rải đủ trạng thái Nháp / NV tự ĐG / QL ĐG / Hoàn tất.
- Mỗi phiếu có bộ chỉ tiêu theo vị trí (barista/phục vụ/thu ngân, bếp, ca trưởng, cửa hàng trưởng,
  quản lý vùng, QA, mua hàng & kho, marketing, nhân sự, kế toán, ban giám đốc).
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

rnd = random.Random(20261130)
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
    'crew': [('Thời gian ra món trung bình', 35, '≤ 5 phút/đơn', lambda s: '%s phút' % vn(max(2.5, 7.5 - s / 20))),
             ('Tỷ lệ món làm lại', 25, '≤ 1%', pct_lo(1)),
             ('Điểm khách bí mật (mystery shopper)', 25, '≥ 85 điểm', lambda s: '%d điểm' % round(60 + s * 0.35)),
             ('Chuyên cần & đúng giờ vào ca', 15, '0 lần trễ ca', count_lo('lần trễ'))],
    'kitchen': [('Hao hụt nguyên liệu', 35, '≤ 2% giá trị xuất', pct_lo(2)),
                ('Đúng định lượng công thức chuẩn', 30, '100% món kiểm tra', pct_hi(100)),
                ('Điểm kiểm tra ATTP khu bếp', 20, '≥ 90 điểm', lambda s: '%d điểm' % round(65 + s * 0.3)),
                ('Chuyên cần', 15, '≥ 25/26 công', days(21))],
    'shift': [('Doanh thu ca so với chỉ tiêu', 30, '≥ 100%', pct_hi(100)),
              ('Thời gian ra món của ca', 25, '≤ 5 phút/đơn', lambda s: '%s phút' % vn(max(2.8, 7.2 - s / 22))),
              ('Chênh lệch két cuối ca', 20, '≤ 0,1% doanh thu ca', pct_lo(0.1)),
              ('Checklist mở/đóng ca đầy đủ', 25, '100% ca', okfail)],
    'sm': [('Doanh thu cửa hàng so với chỉ tiêu', 30, '≥ 100%', pct_hi(100)),
           ('Chi phí nguyên liệu (food cost)', 20, '≤ 32% doanh thu', pct_lo(32)),
           ('Chi phí nhân công (labor cost)', 20, '≤ 22% doanh thu', pct_lo(22)),
           ('Điểm kiểm tra vệ sinh – ATTP', 15, '≥ 90 điểm', lambda s: '%d điểm' % round(65 + s * 0.3)),
           ('Tỷ lệ nghỉ việc của cửa hàng', 15, '≤ 6%/tháng', pct_lo(6))],
    'area': [('Doanh thu vùng so với chỉ tiêu', 35, '≥ 100%', pct_hi(100)),
             ('Biên lợi nhuận cửa hàng bình quân', 25, '≥ 15%', pct_hi(15)),
             ('Cửa hàng đạt điểm kiểm tra ≥ 90', 20, '100% cửa hàng', pct_hi(100)),
             ('Tỷ lệ nghỉ việc toàn vùng', 20, '≤ 6%/tháng', pct_lo(6))],
    'qa': [('Kiểm tra ATTP cửa hàng đúng lịch', 40, '100% lượt', pct_hi(100)),
           ('Mẫu nguyên liệu không đạt', 30, '≤ 1% lô nhập', pct_lo(1)),
           ('Hồ sơ ATTP đầy đủ (giấy khám sức khoẻ, tập huấn)', 30, '100% nhân viên', okfail)],
    'supply': [('Giao hàng đủ, đúng giờ cho cửa hàng', 40, '≥ 98% chuyến', pct_hi(98)),
               ('Chênh lệch kiểm kê kho', 30, '≤ 0,3% giá trị', pct_lo(0.3)),
               ('Hàng hết hạn phải huỷ', 30, '≤ 0,5% giá trị', pct_lo(0.5))],
    'mkt': [('Lượt khách quay lại (thành viên)', 40, '≥ 35% đơn', pct_hi(35)),
            ('Chiến dịch đúng tiến độ', 30, '100% chiến dịch', okfail),
            ('Điểm đánh giá trực tuyến trung bình', 30, '≥ 4,5 sao', lambda s: '%s sao' % vn(3.6 + s / 100))],
    'acct': [('Báo cáo tài chính / thuế đúng hạn', 40, '100% đúng hạn', okfail),
             ('Đối soát doanh thu cửa hàng – ngân hàng', 30, '100% ngày', pct_hi(100)),
             ('Sai sót chứng từ', 30, '≤ 3 lỗi/tháng', count_lo('lỗi'))],
    'hr': [('Tuyển đủ định biên cửa hàng', 35, '≥ 95% định biên', pct_hi(95)),
           ('Tỷ lệ nghỉ việc toàn chuỗi', 30, '≤ 6%/tháng', pct_lo(6)),
           ('Nhân viên mới hoàn thành đào tạo hội nhập', 35, '100% trong 2 tuần', okfail)],
    'exec': [('Doanh thu chuỗi so với kế hoạch', 40, '≥ 100%', pct_hi(100)),
             ('EBITDA cửa hàng', 30, '≥ 18%', pct_hi(18)),
             ('Mở cửa hàng mới đúng tiến độ', 30, 'Theo kế hoạch năm', okfail)],
    'office': [('Hoàn thành công việc đúng hạn', 40, '≥ 95% đầu việc', pct_hi(95)),
               ('Chất lượng sản phẩm bàn giao', 35, 'Không lỗi nghiêm trọng', okfail),
               ('Hỗ trợ cửa hàng', 25, '≤ 1 ngày phản hồi', okfail)],
}


def kind(e):
    j = (e.job_id.name or e.job_title or '').lower()
    for keys, k in [(('giám đốc',), 'exec'), (('quản lý vùng',), 'area'), (('cửa hàng trưởng',), 'sm'),
                    (('ca trưởng',), 'shift'), (('bếp',), 'kitchen'), (('qa',), 'qa'),
                    (('mua hàng', 'kho'), 'supply'), (('marketing', 'nội dung'), 'mkt'),
                    (('kế toán',), 'acct'), (('nhân sự', 'tuyển dụng', 'đào tạo', 'c&b'), 'hr'),
                    (('barista', 'phục vụ', 'thu ngân'), 'crew')]:
        if any(x in j for x in keys):
            return k
    return 'office'


emps = Emp.search([('active', '=', True)], order='id')
ability = {e.id: min(96, max(45, rnd.gauss(76, 9))) for e in emps}
trend = {e.id: rnd.uniform(-0.3, 0.35) for e in emps}   # điểm/tháng: người tiến bộ, người đi xuống
for e in [x for x in emps if kind(x) == 'crew'][5:7]:
    ability[e.id], trend[e.id] = 52, -0.1   # 2 người yếu → có phiếu "Chưa đạt"

SELF_GOOD = ['Hoàn thành tốt các ca, không trễ ca nào.',
             'Đã luyện thêm công thức mới, ra món nhanh hơn.',
             'Cuối tuần đông khách, đã hỗ trợ thêm ca.',
             'Nắm vững quy trình mở/đóng ca sau đào tạo.']
SELF_WEAK = ['Tháng này vướng lịch thi nên đổi ca nhiều, chưa đạt chuyên cần.',
             'Còn làm lại món vào giờ cao điểm, cần luyện thêm.']
MGR = {'excellent': 'Xuất sắc, đề xuất khen thưởng tháng.',
       'good': 'Làm việc tốt, ổn định.',
       'fair': 'Đạt yêu cầu, cần cải thiện tốc độ giờ cao điểm.',
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
    season = -3 if m.month in (1, 2) else (-1.5 if m.month in (6, 7) else 0)  # Tết / mùa thi, nghỉ hè
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
    ('Doanh thu chuỗi %d đạt 95 tỷ đồng' % YEAR, [
        ('Doanh thu toàn chuỗi', 95, 0.97, 'tỷ đồng'),
        ('Cửa hàng mới khai trương', 2, 1.0, 'cửa hàng'),
        ('Doanh thu giao hàng (online)', 25, 0.85, '% doanh thu')]),
    ('Trải nghiệm khách hàng đạt 4,6 sao', [
        ('Điểm đánh giá trực tuyến trung bình', 4.6, 0.98, 'sao'),
        ('Điểm khách bí mật toàn chuỗi', 88, 0.96, 'điểm')]),
    ('Giữ chân nhân viên — nghỉ việc dưới 5%/tháng', [
        ('Tỷ lệ nghỉ việc bình quân tháng', 5, 0.5, '% (càng thấp càng tốt)'),
        ('Ca trưởng đề bạt từ nội bộ', 6, 0.67, 'người'),
        ('Nhân viên đạt chứng nhận pha chế nội bộ', 80, 0.85, '%')]),
]
for (name, krs), pace in zip(COMPANY, ('on', 'on', 'risk')):
    mk_obj(name, 'company', ceo, krs, pace=pace)

DEPT = [
    ('quản lý vùng', 'Vùng đạt doanh thu và biên lợi nhuận kế hoạch', [
        ('Doanh thu vùng so với kế hoạch', 100, 0.97, '%'),
        ('Cửa hàng có lãi', 100, 0.9, '%')]),
    ('bếp trưởng', 'Chuẩn hoá công thức bếp trung tâm', [
        ('Món có công thức chuẩn và định lượng', 100, 1.0, '%'),
        ('Giảm hao hụt nguyên liệu (từ 3%)', 1, 0.7, 'điểm %')]),
    ('trưởng nhóm qa', 'Toàn chuỗi đạt kiểm tra ATTP định kỳ', [
        ('Cửa hàng đạt ≥ 90 điểm kiểm tra', 8, 0.9, 'cửa hàng'),
        ('Nhân viên có hồ sơ sức khoẻ và tập huấn hợp lệ', 100, 1.0, '%')]),
    ('trưởng phòng mua hàng', 'Giảm giá vốn nguyên liệu 3%', [
        ('Nhà cung cấp chính ký giá năm', 5, 1.0, 'nhà cung cấp'),
        ('Giảm giá vốn bình quân', 3, 0.6, '%')]),
    ('trưởng phòng marketing', 'Phát triển chương trình thành viên', [
        ('Thành viên mới', 20000, 0.85, 'thành viên'),
        ('Tỷ lệ đơn từ thành viên', 35, 0.9, '%')]),
    ('kế toán trưởng', 'Đóng sổ tháng trong 5 ngày làm việc', [
        ('Số tháng đóng sổ đúng hạn', 12, 0.92, 'tháng'),
        ('Đối soát doanh thu ngân hàng hằng ngày', 100, 1.0, '%')]),
    ('trưởng phòng nhân sự', 'Tuyển đủ người cho cao điểm Tết', [
        ('Nhân viên bán thời gian tuyển mới', 60, 0.85, 'người'),
        ('Thời gian tuyển bình quân', 7, 0.6, 'ngày (càng thấp càng tốt)'),
        ('Khảo sát hài lòng nhân viên', 80, 0.95, 'điểm')]),
]
DEPT_PACE = ('on', 'done', 'on', 'risk', 'on', 'on', 'risk')
for (kw, name, krs), pace in zip(DEPT, DEPT_PACE):
    mk_obj(name, 'department', who(kw), krs, pace=pace)

# Cá nhân: một số cửa hàng trưởng / ca trưởng / barista
INDIV = [
    ('Hoàn thành khoá Quản lý cửa hàng', [
        ('Số buổi học hoàn thành', 8, 1.0, 'buổi'), ('Đề xuất cải tiến được áp dụng', 2, 0.5, 'đề xuất')]),
    ('Kèm cặp 2 nhân viên mới lên ca trưởng', [
        ('Nhân viên đạt đánh giá ca trưởng', 2, 1.0, 'người')]),
    ('Đạt chứng nhận pha chế nội bộ cấp 2', [
        ('Bài thi thực hành đạt', 1, 1.0, 'bài'), ('Món mới làm thành thạo', 6, 0.83, 'món')]),
    ('Rút thời gian ra món xuống 4 phút', [
        ('Thời gian ra món bình quân (từ 6 phút)', 2, 0.7, 'phút giảm')]),
    ('Học latte art cơ bản', [
        ('Giờ thực hành', 20, 1.0, 'giờ'), ('Mẫu vẽ thành thạo', 3, 0.67, 'mẫu')]),
]
leads = [e for e in emps if kind(e) in ('sm', 'shift')][:6]
workers = [e for e in emps if kind(e) == 'crew']
rnd.shuffle(workers)
targets = [(leads[i % len(leads)], INDIV[i % 2]) for i in range(len(leads))] + \
          [(w, INDIV[2 + i % 3]) for i, w in enumerate(workers[:10])]
for i, (e, (name, krs)) in enumerate(targets):
    mk_obj('%s — %s' % (name, e.name), 'individual', e, krs,
           pace='done' if i % 4 == 1 else 'risk' if i % 5 == 3 else 'on')

# Năm trước: đã đóng
PREV = [
    ('Doanh thu chuỗi %d đạt 80 tỷ đồng' % (YEAR - 1), 'company', ceo, [
        ('Doanh thu', 80, 1.03, 'tỷ đồng'), ('Cửa hàng mới', 2, 1.0, 'cửa hàng')]),
    ('Mở vùng Hà Nội (3 cửa hàng)', 'company', ceo, [
        ('Cửa hàng khai trương', 3, 1.0, 'cửa hàng'), ('Tuyển đủ nhân viên vùng Hà Nội', 24, 0.9, 'người')]),
    ('Số hoá chấm công qua điện thoại', 'department', who('trưởng phòng nhân sự'), [
        ('Nhân viên dùng ứng dụng chấm công', 100, 1.0, '%'), ('Bảng công tự động', 12, 0.75, 'tháng')]),
    ('Giảm hàng huỷ do hết hạn', 'department', who('trưởng phòng mua hàng'), [
        ('Giảm giá trị hàng huỷ', 30, 0.8, '%')]),
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

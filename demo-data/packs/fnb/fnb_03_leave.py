# -*- coding: utf-8 -*-
"""SEED DEMO F&B — Nghỉ phép (chuỗi cà phê, năm hiện tại; bản chỉnh từ seed_leave_demo.py).

- Phân bổ phép năm cho mọi nhân viên đang làm: 12 ngày + 1 ngày mỗi đủ 5 năm thâm niên
  (Bộ luật Lao động 2019, Điều 113–114). Cần l10n_vn_hr >= 19.0.1.2.0 (vn_seniority_date).
- Đơn nghỉ: phép năm, nghỉ ốm, việc riêng có lương (kết hôn / tang — Điều 115), nghỉ không lương,
  thai sản 6 tháng. Đã duyệt (quá khứ), chờ duyệt (sắp tới), vài đơn bị từ chối.
- Tránh kỳ Tết Âm lịch (10/2 – 25/2) và cuối tuần; không trùng ngày trong cùng một người.
- Loại "Nghỉ không lương", "Nghỉ việc riêng có lương", "Nghỉ chế độ thai sản" chuyển sang
  KHÔNG cần phân bổ (nghỉ theo sự kiện / thoả thuận, không có quỹ ngày).
- Không gửi email: xoá thư đi phát sinh trong lúc seed.

Chỉ là DỮ LIỆU MẪU. Hạt giống cố định. Chạy lại: bỏ qua nếu DB đã có hơn 10 đơn nghỉ.

Run (VPS):
  docker run ... odoo shell -d demo --no-http < demo-data/packs/seed_leave_demo.py
"""
import random
from datetime import date, timedelta

from odoo import fields

rnd = random.Random(20261129)
today = fields.Date.today()
YEAR = today.year
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True,
           mail_activity_automation_skip=True, leave_skip_state_check=True)
Leave = env['hr.leave'].sudo().with_context(**ctx)
Alloc = env['hr.leave.allocation'].sudo().with_context(**ctx)
Type = env['hr.leave.type'].sudo()
Emp = env['hr.employee'].sudo()
mail_before = env['mail.mail'].sudo().search([], order='id desc', limit=1).id or 0

if Leave.search_count([]) > 10:
    print('Đã seed nghỉ phép trước đó — bỏ qua.')
    raise SystemExit


def ltype(name):
    t = Type.with_context(lang='vi_VN').search([('name', '=', name), ('country_id', '=', False)], limit=1)
    assert t, name
    return t


T_ANNUAL = ltype('Nghỉ phép năm')
T_UNPAID = ltype('Nghỉ không lương')
T_PERSONAL = ltype('Nghỉ việc riêng có lương')
T_MATERNITY = ltype('Nghỉ chế độ thai sản')
T_SICK = Type.browse(env.ref('hr_holidays.leave_type_sick_time_off').id)
(T_UNPAID | T_PERSONAL | T_MATERNITY).write({'requires_allocation': False})

emps = Emp.search([('active', '=', True)], order='id')
# Tài khoản demo (khách tham quan) đóng vai người duyệt nghỉ phép của mọi nhân viên,
# để "Đội của tôi" / "Chờ tôi duyệt" có dữ liệu khi khách đăng nhập demo.
demo_user = env['res.users'].sudo().search([('login', '=', 'demo')], limit=1)
if demo_user:
    emps.write({'leave_manager_id': demo_user.id})
busy = {e.id: set() for e in emps}           # ngày đã có đơn của từng người
TET = (date(YEAR, 2, 10), date(YEAR, 2, 25))


def workdays(start, n):
    """n ngày làm việc liên tiếp từ start (bỏ T7, CN)."""
    d, out = start, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def free_slot(e, n, lo, hi, tries=40):
    for _ in range(tries):
        start = lo + timedelta(days=rnd.randint(0, max((hi - lo).days, 0)))
        days = workdays(start, n)
        if any(TET[0] <= d <= TET[1] for d in days) or (n <= 20 and days[-1] > hi + timedelta(days=7)):
            continue
        if not (set(days) & busy[e.id]):
            busy[e.id] |= set(days)
            return days[0], days[-1]
    return None


stats = {}


def mk(e, t, n, lo, hi, reason, state):
    slot = free_slot(e, n, lo, hi)
    if not slot:
        return None
    try:
        with env.cr.savepoint():
            lv = Leave.create({'employee_id': e.id, 'holiday_status_id': t.id,
                               'request_date_from': slot[0], 'request_date_to': slot[1],
                               'private_name': reason})
            if lv.state == 'confirm' and state in ('validate', 'refuse'):
                lv.action_approve(check_state=False)
                if lv.state == 'validate1':
                    lv.action_approve(check_state=False)
            if state == 'refuse':
                lv.action_refuse()
    except Exception as ex:  # noqa: BLE001 — seed: bỏ qua đơn lỗi, ghi lại
        print('  bỏ đơn', e.name, t.name, slot, '→', str(ex).splitlines()[0][:120])
        busy[e.id] -= set(workdays(slot[0], n))
        return None
    key = (t.name, lv.state)
    stats[key] = stats.get(key, 0) + 1
    return lv


# ── 1. Phân bổ phép năm ──────────────────────────────────
y0, y1 = date(YEAR, 1, 1), date(YEAR, 12, 31)
alloc_days = {}
for e in emps:
    sen_start = e.vn_seniority_date
    years = (y1 - sen_start).days // 365 if sen_start else 0
    days = 12 + years // 5
    if sen_start and sen_start > y0:   # vào giữa năm: theo tỷ lệ tháng
        days = round(12 * (13 - sen_start.month) / 12)
    alloc_days[e.id] = days
    if days <= 0:
        continue
    old = Alloc.search([('employee_id', '=', e.id), ('holiday_status_id', '=', T_ANNUAL.id)])
    if old:
        old.write({'date_from': y0, 'date_to': y1, 'number_of_days': days,
                   'name': 'Phép năm %d' % YEAR})
        continue
    vals = {'name': 'Phép năm %d' % YEAR, 'employee_id': e.id,
            'holiday_status_id': T_ANNUAL.id, 'allocation_type': 'regular',
            'date_from': y0, 'date_to': y1, 'number_of_days': days}
    al = Alloc.create({k: v for k, v in vals.items() if k in Alloc._fields})
    if al.state != 'validate':
        al.action_approve()
print('Phân bổ phép năm:', Alloc.search_count([('holiday_status_id', '=', T_ANNUAL.id)]))

# ── 2. Đơn nghỉ ──────────────────────────────────────────
past_lo, past_hi = date(YEAR, 1, 5), today - timedelta(days=3)
fut_lo, fut_hi = today + timedelta(days=3), min(today + timedelta(days=50), date(YEAR, 12, 21))
# thai sản 6 tháng: nữ nhân viên đã kết hôn, 22–34 tuổi
moms = emps.filtered(lambda x: x.sex == 'female' and x.marital == 'married' and 22 <= x.vn_age <= 34)
for e, (lo, state) in zip(moms[:2], [(today - timedelta(days=75), 'validate'),
                                      (today + timedelta(days=20), 'confirm')]):
    if Leave.search_count([('employee_id', '=', e.id), ('state', 'not in', ('refuse', 'cancel'))]):
        continue
    mk(e, T_MATERNITY, 130, lo, lo, 'Nghỉ sinh con (6 tháng)', state)

emps -= moms[:2]   # người nghỉ thai sản không có đơn khác

ANNUAL_REASONS = ['Thi học kỳ', 'Về quê thăm gia đình', 'Đi du lịch cùng gia đình', 'Việc gia đình',
                  'Đưa con đi khám', 'Sửa nhà', 'Nghỉ ngơi', 'Đám cưới người thân',
                  'Làm giấy tờ cá nhân']
SICK_REASONS = ['Sốt, cảm cúm', 'Đau dạ dày', 'Viêm họng', 'Khám và điều trị răng', 'Sốt xuất huyết']

for e in emps:
    budget = alloc_days.get(e.id, 0)
    start_ok = max(past_lo, e.vn_seniority_date or past_lo)
    # phép năm đã duyệt trong quá khứ: 1–3 đơn, mỗi đơn 1–3 ngày
    for _ in range(rnd.choice((1, 1, 2, 2, 3))):
        n = rnd.choice((1, 1, 2, 3))
        if budget - n < 2 or start_ok >= past_hi:
            break
        if mk(e, T_ANNUAL, n, start_ok, past_hi, rnd.choice(ANNUAL_REASONS), 'validate'):
            budget -= n
    # nghỉ ốm (≈ 30 % số người)
    if rnd.random() < 0.3 and start_ok < past_hi:
        mk(e, T_SICK, rnd.choice((1, 1, 2, 3)), start_ok, past_hi, rnd.choice(SICK_REASONS), 'validate')
    alloc_days[e.id] = budget

# đơn phép năm sắp tới: chờ duyệt / đã duyệt / bị từ chối
pool = list(emps)
rnd.shuffle(pool)
for i, e in enumerate(pool[:32]):
    n = rnd.choice((1, 2, 3, 5))
    if alloc_days.get(e.id, 0) < n:
        continue
    state = 'confirm' if i < 24 else ('refuse' if i < 27 else 'validate')
    reason = rnd.choice(ANNUAL_REASONS) if state != 'refuse' else 'Trùng lịch cao điểm cuối tuần tại cửa hàng'
    if mk(e, T_ANNUAL, n, fut_lo, fut_hi, reason, state):
        alloc_days[e.id] -= n

# việc riêng có lương (kết hôn 3 ngày, tang 3 ngày, con kết hôn 1 ngày)
for e, (n, reason, past) in zip(pool[32:38], [(3, 'Kết hôn', True), (3, 'Bố mất', True),
                                              (1, 'Con kết hôn', True), (3, 'Kết hôn', False),
                                              (3, 'Mẹ vợ mất', True), (1, 'Con kết hôn', False)]):
    lo, hi = (past_lo, past_hi) if past else (fut_lo, fut_hi)
    mk(e, T_PERSONAL, n, lo, hi, reason, 'validate' if past else 'confirm')

# nghỉ không lương
for e in pool[38:42]:
    mk(e, T_UNPAID, rnd.choice((2, 3, 5)), past_lo, past_hi, 'Việc riêng (thoả thuận nghỉ không lương)', 'validate')

env.flush_all()
# không gửi email nào từ seed
junk = env['mail.mail'].sudo().search([('id', '>', mail_before)])
print('Xoá thư đi phát sinh:', len(junk))
junk.unlink()
env.cr.commit()

for (t, s), c in sorted(stats.items()):
    print('%-28s %-10s %d' % (t, s, c))
print('Tổng đơn:', Leave.search_count([]), '— chờ duyệt:', Leave.search_count([('state', '=', 'confirm')]))

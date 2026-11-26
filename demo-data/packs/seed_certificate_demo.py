# -*- coding: utf-8 -*-
"""SEED DEMO — Chứng chỉ nhân viên cho demo (công ty may mặc).

- ATVSLĐ (bắt buộc; nhóm 1–3 hạn 24 tháng, nhóm 4 hằng năm — 12 tháng) cho mọi nhân viên theo các khoá huấn luyện của công ty:
  một khoá cũ đã hết hạn, một khoá sắp hết hạn trong 60 ngày, các khoá còn hạn, khoá cho người mới.
- PCCC (đội PCCC cơ sở), Sơ cấp cứu (tổ trưởng, nhân sự), vận hành nồi hơi / an toàn điện
  (cơ điện, là hơi), xe nâng (kho), tay nghề máy may công nghiệp, nghiệp vụ QC, kế toán trưởng,
  bằng tốt nghiệp (theo trình độ trên hồ sơ), ngoại ngữ, giấy phép lái xe.
- Chạy cron nhắc hạn → việc cần làm cho chứng chỉ sắp / đã hết hạn. Không gửi email.

Chỉ là DỮ LIỆU MẪU. Hạt giống cố định. Chạy lại: bỏ qua nếu đã có hơn 10 chứng chỉ.

Run (VPS):
  docker run ... odoo shell -d demo --no-http < demo-data/packs/seed_certificate_demo.py
"""
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields

rnd = random.Random(20261128)
today = fields.Date.today()
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True)
Cert = env['sapiones.hr.certificate'].sudo().with_context(**ctx)
Type = env['sapiones.hr.certificate.type'].sudo()
Emp = env['hr.employee'].sudo()
mail_before = env['mail.mail'].sudo().search([], order='id desc', limit=1).id or 0

if Cert.with_context(active_test=False).search_count([]) > 10:
    print('Đã seed chứng chỉ trước đó — bỏ qua.')
    raise SystemExit


def T(xmlid):
    return env.ref('sapiones_hr_certificate.' + xmlid)


def ttype(name, category, months=0):
    t = Type.search([('name', '=', name)], limit=1)
    return t or Type.create({'name': name, 'category': category, 'default_validity_months': months})


ATLD, PCCC, SCC = T('ctype_atld'), T('ctype_pccc'), T('ctype_socapcuu')
NOIHOI, ANDIEN, XENANG = T('ctype_noihoi'), T('ctype_andien'), T('ctype_xenang')
BAOTRI, BANG, NN, LAIXE = T('ctype_baotri'), T('ctype_bangcap'), T('ctype_ngoaingu'), T('ctype_lai_xe')
MAY = ttype('Vận hành máy may công nghiệp', 'professional')
QC = ttype('Nghiệp vụ kiểm tra chất lượng (QC) may mặc', 'professional')
KTT = ttype('Chứng chỉ kế toán trưởng', 'professional')

# Loại "An toàn lao động (ATLĐ)" tạo tay trùng với ATVSLĐ của module → gộp về ATVSLĐ, lưu trữ
dup = Type.search([('name', '=', 'An toàn lao động (ATLĐ)'), ('id', '!=', ATLD.id)])
if dup:
    Cert.with_context(active_test=False).search([('type_id', 'in', dup.ids)]).write({'type_id': ATLD.id})
    dup.write({'active': False})
Cert.search([('type_id', '=', False), ('name', 'ilike', 'an toàn lao động')]).write({'type_id': ATLD.id})

emps = Emp.search([('active', '=', True)], order='id')


def job(e):
    return (e.job_id.name or e.job_title or '').lower()


def has(e, t):
    return Cert.with_context(active_test=False).search_count([('employee_id', '=', e.id), ('type_id', '=', t.id)])


stats = {}


def mk(e, t, issued, number, org, name=None, expiry='auto', note=False):
    if has(e, t):
        return
    if expiry == 'auto':
        expiry = issued + relativedelta(months=t.default_validity_months) if t.default_validity_months else False
    Cert.create({'employee_id': e.id, 'type_id': t.id, 'name': name or t.name, 'number': number,
                 'issuing_organization': org, 'date_issued': issued, 'date_expiry': expiry, 'note': note})
    stats[t.name] = stats.get(t.name, 0) + 1


def start_of(e):
    return e.vn_seniority_date or date(today.year - 3, 1, 1)


# ── 1. ATVSLĐ: các khoá huấn luyện của công ty ──────────
ORG_ATLD = 'Đơn vị huấn luyện ATVSLĐ (được Sở LĐ-TB&XH cấp phép)'
courses = [date(today.year - 2, 10, 14),                       # → đã hết hạn
           today - relativedelta(years=2) + timedelta(days=24),  # → sắp hết hạn (< 60 ngày)
           date(today.year - 1, 6, 20), date(today.year, 3, 12), date(today.year, 8, 12)]
pool = list(emps)
rnd.shuffle(pool)
for i, e in enumerate(pool):
    s = start_of(e)
    eligible = [c for c in courses if c >= s - timedelta(days=5)] or [courses[0]]
    if s > today - timedelta(days=60):
        continue                                   # đang thử việc: chưa được huấn luyện → thiếu ATVSLĐ
    if s <= courses[0] and i < 5:
        c = courses[0]
    elif s <= courses[1] and i < 22:
        c = courses[1]
    else:
        c = rnd.choice(eligible[-3:]) if len(eligible) > 1 else eligible[0]
    group = 'nhóm 1' if any(k in job(e) for k in ('giám đốc', 'chief', 'trưởng phòng', 'kế toán trưởng')) \
        else 'nhóm 2' if 'nhân sự' in job(e) else 'nhóm 3' if any(k in job(e) for k in ('cơ điện', 'kho')) else 'nhóm 4'
    if group == 'nhóm 4':
        # NĐ 44/2016: nhóm 4 huấn luyện định kỳ hằng năm → lớp nhắc lại một năm sau, hạn 12 tháng
        if c + relativedelta(years=1) <= today:
            c = c + relativedelta(years=1)
        mk(e, ATLD, c, 'ATVSLĐ/4/%d-%03d' % (c.year, i + 1), ORG_ATLD,
           name='Huấn luyện ATVSLĐ nhóm 4', expiry=c + relativedelta(months=12),
           note='Nhóm 4: huấn luyện định kỳ hằng năm (NĐ 44/2016/NĐ-CP).')
    else:
        mk(e, ATLD, c, 'ATVSLĐ/%s/%d-%03d' % (group.split()[1], c.year, i + 1), ORG_ATLD,
           name='Huấn luyện ATVSLĐ %s' % group)

# ── 2. Đội PCCC cơ sở + sơ cấp cứu ─────────────────────
ORG_PCCC = 'Phòng Cảnh sát PCCC & CNCH — Công an tỉnh'
leads = [e for e in emps if 'trưởng' in job(e) or 'thủ kho' in job(e)]
sewers = [e for e in emps if job(e).startswith('công nhân')]
rnd.shuffle(sewers)
for i, e in enumerate(leads + sewers[:6]):
    d = date(today.year - 1, 4, 8) if i % 3 else date(today.year - 2, 12, 5)   # một phần sắp/đã hết hạn
    mk(e, PCCC, d, 'PCCC-%d/%04d' % (d.year, 120 + i), ORG_PCCC, name='Nghiệp vụ PCCC cơ sở')
for i, e in enumerate([x for x in emps if 'tổ trưởng' in job(x) or 'chuyền trưởng' in job(x) or 'nhân sự' in job(x)]):
    d = date(today.year - 1, 9, 16)
    mk(e, SCC, d, 'SCC-%d/%03d' % (d.year, 40 + i), 'Trung tâm Y tế huyện — Hội Chữ thập đỏ', name='Sơ cấp cứu tại nơi làm việc')

# ── 3. Thiết bị có yêu cầu nghiêm ngặt về ATLĐ ──────────
ORG_KD = 'Trung tâm Kiểm định kỹ thuật an toàn khu vực'
for e in emps:
    j = job(e)
    if 'cơ điện' in j:
        mk(e, NOIHOI, date(today.year - 3, 5, 6), 'NH-%d/0217' % (today.year - 3), ORG_KD,
           name='Vận hành nồi hơi cho hệ thống là hơi')
        mk(e, ANDIEN, today - relativedelta(months=12) + timedelta(days=18), 'AD-BAC4/%d-033' % (today.year - 1),
           ORG_ATLD, name='An toàn điện — bậc 4/5')
        mk(e, BAOTRI, date(today.year - 6, 7, 1), 'BT-%d-1182' % (today.year - 6),
           'Trường Cao đẳng Kỹ thuật', name='Kỹ thuật bảo trì cơ điện', expiry=False)
    if 'hoàn thiện' in j and 'tổ trưởng' in j:
        mk(e, NOIHOI, date(today.year - 2, 2, 27), 'NH-%d/0388' % (today.year - 2), ORG_KD,
           name='Vận hành nồi hơi cho hệ thống là hơi')
    if 'thủ kho' in j:
        mk(e, XENANG, today - relativedelta(years=5) - timedelta(days=12), 'XN-%d/0591' % (today.year - 5), ORG_KD,
           name='Vận hành xe nâng hàng', note='Đã hết hạn — đăng ký học lại khoá tháng tới.')

# ── 4. Nghề, nghiệp vụ, bằng cấp ────────────────────────
for i, e in enumerate(sewers[:int(len(sewers) * 0.55)]):
    lvl = rnd.choice(('bậc 2/7', 'bậc 3/7', 'bậc 3/7', 'bậc 4/7'))
    d = max(start_of(e), date(today.year - 8, 1, 1)) + timedelta(days=rnd.randint(20, 200))
    if d < today:
        mk(e, MAY, d, 'TN-MAY/%d-%04d' % (d.year, 300 + i), 'Trường Trung cấp nghề Dệt may',
           name='Tay nghề may công nghiệp %s' % lvl, expiry=False)
for i, e in enumerate([x for x in emps if 'qc' in job(x)]):
    mk(e, QC, date(today.year - 2, 6, 3), 'QC-%d-%03d' % (today.year - 2, 57 + i),
       'Viện Dệt may — Trung tâm đào tạo', name='Nghiệp vụ QC may mặc (AQL)', expiry=False)
for e in emps.filtered(lambda x: 'kế toán trưởng' in job(x)):
    mk(e, KTT, date(today.year - 7, 11, 20), 'KTT-%d/1046' % (today.year - 7),
       'Trường Đại học Kinh tế — khoá bồi dưỡng kế toán trưởng', expiry=False)

DEG = {'graduate': 'Bằng tốt nghiệp Cao đẳng', 'bachelor': 'Bằng Cử nhân / Kỹ sư', 'master': 'Bằng Thạc sĩ'}
SCHOOL = ['Trường Đại học Kinh tế', 'Trường Đại học Bách khoa', 'Trường Đại học Công nghiệp',
          'Trường Cao đẳng Công nghệ Dệt may', 'Trường Đại học Mở', 'Trường Đại học Ngoại thương']
for i, e in enumerate(emps.filtered(lambda x: x.certificate in DEG and not job(x).startswith('công nhân'))):
    y = (e.birthday.year + 22) if e.birthday else today.year - 10
    mk(e, BANG, date(y, 7, rnd.randint(1, 28)), 'VB-%d-%05d' % (y, rnd.randint(10000, 99999)),
       rnd.choice(SCHOOL), name=DEG[e.certificate], expiry=False)

# ── 5. Ngoại ngữ, lái xe ────────────────────────────────
LANG = [('TOEIC 750', 'IIG Việt Nam'), ('IELTS 6.5', 'British Council'), ('TOEIC 820', 'IIG Việt Nam'),
        ('JLPT N2 (tiếng Nhật)', 'Japan Foundation'), ('TOPIK 4 (tiếng Hàn)', 'NIIED')]
# chỉ người Việt (tên có dấu) — nhân viên tên nước ngoài không cần TOEIC/IELTS
for i, e in enumerate(emps.filtered(lambda x: not x.name.isascii() and any(k in job(x) for k in
                                                   ('giám đốc', 'chief', 'kinh doanh', 'nhân sự', 'qc')))):
    name, org = LANG[i % len(LANG)]
    d = today - relativedelta(months=rnd.choice((8, 15, 22, 26)))
    mk(e, NN, d, '%s-%06d' % (name.split()[0], rnd.randint(100000, 999999)), org, name=name)
for e in emps.filtered(lambda x: any(k in job(x) for k in ('giám đốc', 'kinh doanh', 'thủ kho'))):
    d = date(today.year - rnd.randint(2, 9), rnd.randint(1, 12), rnd.randint(1, 28))
    mk(e, LAIXE, d, '79%010d' % rnd.randint(10 ** 9, 10 ** 10 - 1), 'Sở Giao thông vận tải', name='Giấy phép lái xe hạng B')

env.flush_all()
# ── Nhắc hạn: việc cần làm cho chứng chỉ sắp / đã hết hạn ─
n_act = Cert._cron_expiry_reminder()
env.flush_all()
junk = env['mail.mail'].sudo().search([('id', '>', mail_before)])
print('Xoá thư đi phát sinh:', len(junk))
junk.unlink()
env.cr.commit()

C = Cert.search([])
print('Theo loại:', sorted(stats.items(), key=lambda x: -x[1]))
print('Tổng chứng chỉ:', len(C), '— việc nhắc hạn mới:', n_act)
print('Trạng thái:', {s: len(C.filtered(lambda c: c.state == s)) for s in ('valid', 'expiring', 'expired', 'no_expiry')})
print('NV chưa có ATVSLĐ:', len(emps.filtered(lambda e: not has(e, ATLD))))

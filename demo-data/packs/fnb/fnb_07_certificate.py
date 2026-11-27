# -*- coding: utf-8 -*-
"""SEED DEMO F&B — Chứng chỉ nhân viên (chuỗi cà phê).

Căn cứ đã tra (27/11/2026):
- Kiến thức ATTP: chủ cơ sở TỰ TỔ CHỨC tập huấn và xác nhận danh sách người đã tập huấn
  (NĐ 155/2018/NĐ-CP sửa NĐ 15/2018); không còn giấy xác nhận do cơ quan nhà nước cấp, KHÔNG có thời hạn
  quy định → chứng chỉ không thời hạn, đơn vị cấp = chính công ty.
  (NĐ 46/2026/NĐ-CP thay NĐ 15/2018 đang bị tạm ngưng áp dụng.)
- Khám sức khoẻ: ít nhất 1 lần/năm (Luật ATVSLĐ 84/2015/QH13, Điều 21) → hạn 12 tháng.
- ATVSLĐ: NĐ 44/2016/NĐ-CP — nhóm 4 huấn luyện định kỳ hằng năm; nhóm 1–3 hạn 24 tháng.
- PCCC, sơ cấp cứu: theo thời hạn mặc định của loại chứng chỉ trong module.
- Chứng nhận pha chế: chứng nhận NỘI BỘ của công ty mẫu (hạn 24 tháng theo quy định nội bộ).
Chỉ là DỮ LIỆU MẪU. Hạt giống cố định. Chạy lại: bỏ qua nếu đã có hơn 10 chứng chỉ.
"""
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields

rnd = random.Random(20261132)
today = fields.Date.today()
ctx = dict(tracking_disable=True, mail_notrack=True, mail_create_nolog=True)
Cert = env['sapiones.hr.certificate'].sudo().with_context(**ctx)
Type = env['sapiones.hr.certificate.type'].sudo()
Emp = env['hr.employee'].sudo()
mail_before = env['mail.mail'].sudo().search([], order='id desc', limit=1).id or 0
COMPANY = env.company.name

if Cert.with_context(active_test=False).search_count([]) > 10:
    print('Đã seed chứng chỉ trước đó — bỏ qua.')
    raise SystemExit


def T(xmlid):
    return env.ref('sapiones_hr_certificate.' + xmlid)


def ttype(name, category, months=0, code=False, mandatory=False):
    t = Type.search([('name', '=', name)], limit=1)
    vals = {'name': name, 'category': category, 'default_validity_months': months}
    if code and 'code' in Type._fields:
        vals['code'] = code
    if 'mandatory' in Type._fields:
        vals['mandatory'] = mandatory
    return t or Type.create(vals)


ATLD, PCCC, SCC = T('ctype_atld'), T('ctype_pccc'), T('ctype_socapcuu')
BANG, NN, LAIXE = T('ctype_bangcap'), T('ctype_ngoaingu'), T('ctype_lai_xe')
ATTP = ttype('Tập huấn kiến thức an toàn thực phẩm', 'safety', 0, 'ATTP', True)
KSK = ttype('Khám sức khoẻ định kỳ', 'safety', 12, 'KSK', True)
PHACHE = ttype('Chứng nhận pha chế nội bộ', 'professional', 24, 'PHACHE')
# loại nhà máy không dùng ở chuỗi F&B → lưu trữ cho danh mục gọn
Type.search([('id', 'in', [T(x).id for x in ('ctype_noihoi', 'ctype_caughtruc', 'ctype_han', 'ctype_baotri')
                            if env.ref('sapiones_hr_certificate.' + x, raise_if_not_found=False)])]).write({'active': False})
# loại ngành may còn sót trong DB mẫu (sapiones_tpl) → lưu trữ
Type.search([('name', 'in', ('Vận hành máy may công nghiệp', 'An toàn lao động (ATLĐ)', 'Vận hành cầu trục / cẩu'))]).write({'active': False})

emps = Emp.search([('active', '=', True)], order='id')


def job(e):
    return (e.job_id.name or e.job_title or '').lower()


def food(e):  # người trực tiếp tiếp xúc / chế biến thực phẩm
    return any(k in job(e) for k in ('barista', 'phục vụ', 'thu ngân', 'bếp', 'ca trưởng', 'cửa hàng trưởng', 'qa'))


def has(e, t):
    return Cert.with_context(active_test=False).search_count([('employee_id', '=', e.id), ('type_id', '=', t.id)])


stats = {}


def mk(e, t, issued, number, org, name=None, expiry='auto', note=False):
    if has(e, t) or issued > today:
        return
    if expiry == 'auto':
        expiry = issued + relativedelta(months=t.default_validity_months) if t.default_validity_months else False
    Cert.create({'employee_id': e.id, 'type_id': t.id, 'name': name or t.name, 'number': number,
                 'issuing_organization': org, 'date_issued': issued, 'date_expiry': expiry, 'note': note})
    stats[t.name] = stats.get(t.name, 0) + 1


def start_of(e):
    return e.vn_seniority_date or date(today.year - 2, 1, 1)


new = lambda e: start_of(e) > today - timedelta(days=45)   # mới vào: chưa kịp tập huấn / khám

# ── 1. Tập huấn ATTP (nội bộ, không thời hạn) — mọi người tiếp xúc thực phẩm ─
for i, e in enumerate([x for x in emps if food(x)]):
    if new(e):
        continue
    d = max(start_of(e) + timedelta(days=rnd.randint(3, 20)), date(today.year - 3, 1, 1))
    mk(e, ATTP, d, 'ATTP-NB/%d-%03d' % (d.year, i + 1), '%s — tự tổ chức tập huấn' % COMPANY,
       note='Chủ cơ sở tự tổ chức tập huấn và xác nhận danh sách (NĐ 155/2018/NĐ-CP).')

# ── 2. Khám sức khoẻ định kỳ hằng năm — đợt tháng 3 năm nay; một phần khám tháng 12 năm trước (sắp hết hạn) ─
pool = [x for x in emps if not new(x)]
rnd.shuffle(pool)
for i, e in enumerate(pool):
    if i < 4:
        d = today - relativedelta(months=12) - timedelta(days=rnd.randint(5, 40))  # quá hạn khám
    elif i < 18:
        d = today - relativedelta(months=12) + timedelta(days=rnd.randint(10, 45))  # sắp hết hạn
    else:
        d = date(today.year, 3, rnd.randint(10, 20))
    if d < start_of(e):
        d = start_of(e) + timedelta(days=7)
    mk(e, KSK, d, 'KSK-%d/%04d' % (d.year, 200 + i), 'Phòng khám đa khoa (cơ sở khám sức khoẻ đủ điều kiện)',
       note='Khám định kỳ ít nhất 1 lần/năm (Luật ATVSLĐ 2015, Điều 21).')

# ── 3. ATVSLĐ (NĐ 44/2016): quản lý nhóm 1 (24 tháng), còn lại nhóm 4 (hằng năm) ─
ORG_ATLD = 'Đơn vị huấn luyện ATVSLĐ (được cấp phép)'
for i, e in enumerate(emps):
    if new(e):
        continue
    if any(k in job(e) for k in ('giám đốc', 'trưởng phòng', 'kế toán trưởng', 'quản lý vùng')):
        d = date(today.year - 1, 5, 14) if i % 3 else date(today.year - 2, 12, 9)
        mk(e, ATLD, d, 'ATVSLĐ/1/%d-%03d' % (d.year, i + 1), ORG_ATLD, name='Huấn luyện ATVSLĐ nhóm 1')
    else:
        d = date(today.year, 4, 18) if i % 5 else today - relativedelta(years=1) + timedelta(days=rnd.randint(8, 30))
        if d < start_of(e):
            d = date(today.year, 8, 22)
        mk(e, ATLD, d, 'ATVSLĐ/4/%d-%03d' % (d.year, i + 1), ORG_ATLD, name='Huấn luyện ATVSLĐ nhóm 4',
           expiry=d + relativedelta(months=12), note='Nhóm 4: huấn luyện định kỳ hằng năm (NĐ 44/2016/NĐ-CP).')

# ── 4. PCCC + sơ cấp cứu: cửa hàng trưởng, ca trưởng, bếp ─
ORG_PCCC = 'Phòng Cảnh sát PCCC & CNCH — Công an thành phố'
keys = [x for x in emps if any(k in job(x) for k in ('cửa hàng trưởng', 'ca trưởng', 'bếp trưởng', 'bếp chính', 'kho'))]
for i, e in enumerate(keys):
    d = date(today.year - 1, 4, 8) if i % 4 else date(today.year - 2, 12, 5)   # một phần sắp/đã hết hạn
    mk(e, PCCC, d, 'PCCC-%d/%04d' % (d.year, 120 + i), ORG_PCCC, name='Nghiệp vụ PCCC cơ sở')
for i, e in enumerate([x for x in emps if any(k in job(x) for k in ('cửa hàng trưởng', 'ca trưởng', 'đào tạo'))]):
    d = date(today.year - 1, 9, 16) if i % 3 else today - relativedelta(months=24) + timedelta(days=20)
    mk(e, SCC, d, 'SCC-%d/%03d' % (d.year, 40 + i), 'Hội Chữ thập đỏ thành phố', name='Sơ cấp cứu tại nơi làm việc')

# ── 5. Chứng nhận pha chế nội bộ (cấp 1–2) ──────────────
for i, e in enumerate([x for x in emps if any(k in job(x) for k in ('barista', 'ca trưởng', 'cửa hàng trưởng'))]):
    if start_of(e) > today - timedelta(days=120):
        continue
    lvl = 'cấp 2' if any(k in job(e) for k in ('trưởng',)) or i % 3 == 0 else 'cấp 1'
    # lần đánh giá gần nhất trong 30 tháng qua (đánh giá lại mỗi 24 tháng) → phần lớn còn hạn, vài người quá hạn
    d = today - timedelta(days=rnd.choice((40, 120, 250, 400, 520, 610, 700, 760)))
    if d < start_of(e) + timedelta(days=60):
        d = start_of(e) + timedelta(days=60)
    mk(e, PHACHE, d, 'PC-%s/%d-%03d' % (lvl[-1], d.year, i + 1), 'Phòng Nhân sự & Đào tạo — học viện pha chế nội bộ',
       name='Chứng nhận pha chế nội bộ %s' % lvl, note='Chứng nhận nội bộ, đánh giá lại sau 24 tháng.')

# ── 6. Bằng cấp, ngoại ngữ (cửa hàng khu du lịch + văn phòng), lái xe ─
DEG = {'graduate': 'Bằng tốt nghiệp Cao đẳng', 'bachelor': 'Bằng Cử nhân', 'master': 'Bằng Thạc sĩ'}
SCHOOL = ['Trường Đại học Kinh tế', 'Trường Đại học Công nghiệp Thực phẩm', 'Trường Cao đẳng Du lịch',
          'Trường Đại học Mở', 'Trường Đại học Thương mại', 'Trường Cao đẳng Kinh tế – Kỹ thuật']
for e in emps.filtered(lambda x: x.certificate in DEG and not food(x) or (x.certificate in DEG and 'trưởng' in job(x))):
    y = (e.birthday.year + 22) if e.birthday else today.year - 8
    if y < today.year:
        mk(e, BANG, date(y, 7, rnd.randint(1, 28)), 'VB-%d-%05d' % (y, rnd.randint(10000, 99999)),
           rnd.choice(SCHOOL), name=DEG[e.certificate], expiry=False)
LANG = [('TOEIC 650', 'IIG Việt Nam'), ('IELTS 6.0', 'British Council'), ('TOEIC 750', 'IIG Việt Nam')]
tour = emps.filtered(lambda x: x.department_id.name in ('Cửa hàng Hoàn Kiếm', 'Cửa hàng Quận 1') and food(x))
office = emps.filtered(lambda x: any(k in job(x) for k in ('giám đốc', 'marketing', 'quản lý vùng')))
for i, e in enumerate(tour[:6] | office):
    name, org = LANG[i % len(LANG)]
    d = today - relativedelta(months=rnd.choice((6, 14, 20, 25)))
    mk(e, NN, d, '%s-%06d' % (name.split()[0], rnd.randint(100000, 999999)), org, name=name)
for e in emps.filtered(lambda x: any(k in job(x) for k in ('kho', 'mua hàng', 'quản lý vùng'))):
    d = date(today.year - rnd.randint(2, 9), rnd.randint(1, 12), rnd.randint(1, 28))
    mk(e, LAIXE, d, '79%010d' % rnd.randint(10 ** 9, 10 ** 10 - 1), 'Sở Xây dựng (quản lý GPLX)', name='Giấy phép lái xe hạng B')

env.flush_all()
n_act = Cert._cron_expiry_reminder()
env.flush_all()
junk = env['mail.mail'].sudo().search([('id', '>', mail_before)])
junk.unlink()
env.cr.commit()

C = Cert.search([])
print('Theo loại:', sorted(stats.items(), key=lambda x: -x[1]))
print('Tổng chứng chỉ:', len(C), '— việc nhắc hạn mới:', n_act)
print('Trạng thái:', {s: len(C.filtered(lambda c: c.state == s)) for s in ('valid', 'expiring', 'expired', 'no_expiry')})
print('Người tiếp xúc thực phẩm chưa có ATTP / khám SK:',
      len(emps.filtered(lambda e: food(e) and not has(e, ATTP))), '/', len(emps.filtered(lambda e: not has(e, KSK))))

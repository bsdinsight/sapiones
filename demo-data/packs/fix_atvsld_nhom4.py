# -*- coding: utf-8 -*-
"""Sửa dữ liệu demo đã seed: chứng chỉ ATVSLĐ nhóm 4 phải huấn luyện lại hằng năm (NĐ 44/2016).

Bản seed đầu để nhóm 4 hạn 24 tháng. Sửa đúng như seed_certificate_demo.py hiện tại:
lớp nào cách nay hơn một năm thì dời lên lớp nhắc lại một năm sau, hạn = ngày cấp + 12 tháng.
Chạy lại an toàn (đã có ghi chú nhóm 4 thì bỏ qua).
"""
from dateutil.relativedelta import relativedelta
from odoo import fields

today = fields.Date.today()
NOTE = 'Nhóm 4: huấn luyện định kỳ hằng năm (NĐ 44/2016/NĐ-CP).'
Cert = env['sapiones.hr.certificate'].sudo().with_context(tracking_disable=True, mail_notrack=True)
done = 0
for c in Cert.with_context(active_test=False).search([('name', '=', 'Huấn luyện ATVSLĐ nhóm 4')]):
    if c.note and 'hằng năm' in str(c.note):
        continue
    d = c.date_issued
    if d + relativedelta(years=1) <= today:
        d = d + relativedelta(years=1)
    num = c.number or ''
    if c.date_issued and str(c.date_issued.year) in num:
        num = num.replace(str(c.date_issued.year), str(d.year), 1)
    c.write({'date_issued': d, 'date_expiry': d + relativedelta(months=12), 'number': num, 'note': NOTE})
    # việc nhắc hạn (nếu có) theo ngày hết hạn mới
    env['mail.activity'].sudo().search([('res_model', '=', c._name), ('res_id', '=', c.id)]).write(
        {'date_deadline': c.date_expiry})
    done += 1
created = Cert._cron_expiry_reminder()
env.cr.commit()
print('Đã sửa %d chứng chỉ nhóm 4; việc nhắc mới: %d' % (done, created))
allc = Cert.search([])
print({s: len(allc.filtered(lambda c: c.state == s)) for s in ('valid', 'expiring', 'expired', 'no_expiry')})

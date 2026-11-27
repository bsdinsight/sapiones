# -*- coding: utf-8 -*-
"""Tính lại phiếu lương demo kỳ 2026 sau khi nạp tham số lương 2026 (sapiones_payroll_vn 19.0.1.2.0).
Phiếu Đã xác nhận → Nháp → Tính → Xác nhận lại. Chỉ dùng cho DỮ LIỆU MẪU."""
slips = env['sapiones.payslip'].sudo().with_context(tracking_disable=True, mail_notrack=True).search(
    [('date_to', '>=', '2026-01-01')])
def tot(s, *codes):
    return sum(s.line_ids.filtered(lambda l: l.code in codes).mapped('amount')) if 'code' in s.line_ids._fields else 0
before = {s.id: s.net for s in slips}
done = slips.filtered(lambda s: s.state == 'done')
slips.action_draft()
slips.action_compute()
done.action_done()
env.cr.commit()
changed = [s for s in slips if abs(s.net - before[s.id]) >= 1]
print('Phiếu 2026: %d, đổi thực lĩnh: %d, tổng thực lĩnh %s → %s' % (
    len(slips), len(changed), '{:,.0f}'.format(sum(before.values())), '{:,.0f}'.format(sum(slips.mapped('net')))))

# -*- coding: utf-8 -*-
"""Tính lại TOÀN BỘ phiếu lương demo sau khi đổi tiền tệ công ty sang VND (số tròn đồng).
Phiếu Đã chốt → Nháp → Tính → Chốt lại. Kiểm: thực lĩnh = tổng thu nhập − BH NLĐ − thuế − khấu trừ khác. Chỉ dùng cho DỮ LIỆU MẪU."""
P = env['sapiones.payslip'].sudo().with_context(tracking_disable=True, mail_notrack=True)
slips = P.search([])
assert slips[:1].currency_id.name in (False, 'VND') or not slips, slips[:1].currency_id.name
before = {s.id: s.net for s in slips}
odd_before = sum(1 for s in slips if s.net != round(s.net) or s.gross != round(s.gross))
done = slips.filtered(lambda s: s.state == 'done')
slips.action_draft()
slips.action_compute()
done.action_done()
env.cr.commit()
env.invalidate_all()
odd = [s.id for s in slips for f in ('gross', 'si_employee', 'pit', 'net', 'employer_cost', 'basic_pay')
       if s[f] != round(s[f])]
odd_lines = slips.mapped('line_ids').filtered(lambda l: l.amount != round(l.amount))
mismatch = [(s.name, s.gross, s.si_employee, s.pit, s.net) for s in slips
            if abs(s.gross - s.si_employee - s.pit - s.other_deduction - s.net) > 0.5]
big = [s.name for s in slips if abs(s.net - before[s.id]) > 1]
print('Phiếu: %d (chốt lại %d) · có số lẻ trước: %d → sau: %d phiếu, %d dòng · lệch cộng trừ: %d · thực lĩnh đổi >1đ: %d'
      % (len(slips), len(done), odd_before, len(set(odd)), len(odd_lines), len(mismatch), len(big)), mismatch[:5], big[:5])
print('Tổng thực lĩnh %s → %s' % ('{:,.2f}'.format(sum(before.values())), '{:,.2f}'.format(sum(slips.mapped('net')))))

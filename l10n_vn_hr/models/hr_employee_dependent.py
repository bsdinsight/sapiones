import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Người phụ thuộc (giảm trừ gia cảnh)'
    _order = 'employee_id, date_birth'

    name = fields.Char(string='Họ và tên', required=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(
        related='employee_id.company_id', string='Công ty', store=True, index=True)
    relationship = fields.Selection([
        ('child', 'Con'),
        ('spouse', 'Vợ/Chồng'),
        ('parent', 'Cha/Mẹ'),
        ('other', 'Khác'),
    ], string='Quan hệ', required=True, default='child')
    date_birth = fields.Date(string='Ngày sinh')
    tax_code = fields.Char(string='MST người phụ thuộc')
    date_from = fields.Date(
        string='Giảm trừ từ',
        help='Tháng bắt đầu tính giảm trừ gia cảnh.')
    date_to = fields.Date(
        string='Giảm trừ đến',
        help='Để trống nếu vẫn đang được tính giảm trừ.')
    is_registered = fields.Boolean(
        string='Đã đăng ký giảm trừ', default=True,
        help='Đã đăng ký người phụ thuộc với cơ quan thuế.')
    note = fields.Char(string='Ghi chú')

    @api.constrains('tax_code')
    def _check_tax_code(self):
        for rec in self:
            if not rec.tax_code:
                continue
            value = rec.tax_code.replace('-', '').strip()
            if not re.fullmatch(r'\d{10}(\d{3})?', value):
                raise ValidationError(
                    _('MST người phụ thuộc phải gồm 10 hoặc 13 chữ số.'))

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    _('“Giảm trừ đến” phải sau hoặc bằng “Giảm trừ từ”.'))

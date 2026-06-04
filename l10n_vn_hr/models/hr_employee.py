import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # --- Giấy tờ tùy thân ---
    vn_id_card = fields.Char(
        string='Số CCCD/CMND', groups='hr.group_hr_user',
        help='Căn cước công dân (12 số) hoặc CMND cũ (9 số).')
    vn_id_card_date = fields.Date(
        string='Ngày cấp', groups='hr.group_hr_user')
    vn_id_card_place = fields.Char(
        string='Nơi cấp', groups='hr.group_hr_user')

    # --- Thuế & Bảo hiểm ---
    vn_tax_code = fields.Char(
        string='MST cá nhân', groups='hr.group_hr_user',
        help='Mã số thuế thu nhập cá nhân (10 chữ số).')
    vn_si_code = fields.Char(
        string='Số sổ BHXH', groups='hr.group_hr_user',
        help='Số sổ bảo hiểm xã hội (10 chữ số).')

    # --- Thông tin khác ---
    vn_hometown = fields.Char(string='Quê quán', groups='hr.group_hr_user')
    vn_ethnicity = fields.Char(string='Dân tộc', groups='hr.group_hr_user')
    vn_religion = fields.Char(string='Tôn giáo', groups='hr.group_hr_user')

    # --- Người phụ thuộc (giảm trừ gia cảnh) ---
    dependent_ids = fields.One2many(
        'hr.employee.dependent', 'employee_id',
        string='Người phụ thuộc', groups='hr.group_hr_user')
    dependent_count = fields.Integer(
        string='Số NPT đã đăng ký', compute='_compute_dependent_count',
        groups='hr.group_hr_user')

    @api.depends('dependent_ids', 'dependent_ids.is_registered')
    def _compute_dependent_count(self):
        for emp in self:
            emp.dependent_count = len(emp.dependent_ids.filtered('is_registered'))

    @api.constrains('vn_id_card')
    def _check_vn_id_card(self):
        for emp in self:
            if emp.vn_id_card and not re.fullmatch(r'\d{9}|\d{12}', emp.vn_id_card.strip()):
                raise ValidationError(_('Số CCCD/CMND phải gồm 9 (CMND) hoặc 12 (CCCD) chữ số.'))

    @api.constrains('vn_tax_code')
    def _check_vn_tax_code(self):
        for emp in self:
            if not emp.vn_tax_code:
                continue
            value = emp.vn_tax_code.replace('-', '').strip()
            if not re.fullmatch(r'\d{10}(\d{3})?', value):
                raise ValidationError(_('MST cá nhân phải gồm 10 hoặc 13 chữ số.'))

    @api.constrains('vn_si_code')
    def _check_vn_si_code(self):
        for emp in self:
            if emp.vn_si_code and not re.fullmatch(r'\d{10}', emp.vn_si_code.strip()):
                raise ValidationError(_('Số sổ BHXH phải gồm đúng 10 chữ số.'))

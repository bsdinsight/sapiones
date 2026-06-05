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

    # --- Địa chỉ riêng theo chuẩn VN (Phường/Xã) ---
    private_country_id = fields.Many2one(
        'res.country',
        default=lambda self: self.env.ref('base.vn', raise_if_not_found=False))
    private_vn_ward_id = fields.Many2one(
        'sapiones.vn.ward', string='Phường / Xã',
        domain="[('state_id', '=?', private_state_id)]", groups='hr.group_hr_user')

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

    @api.onchange('private_state_id')
    def _onchange_private_state_clear_ward(self):
        if self.private_vn_ward_id and self.private_vn_ward_id.state_id != self.private_state_id:
            self.private_vn_ward_id = False

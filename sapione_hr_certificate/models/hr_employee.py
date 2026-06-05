from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certificate_ids = fields.One2many(
        'sapione.hr.certificate', 'employee_id',
        string='Chứng chỉ', groups='hr.group_hr_user')
    certificate_count = fields.Integer(
        compute='_compute_certificate_count', groups='hr.group_hr_user')
    certificate_alert = fields.Boolean(
        string='Có chứng chỉ hết hạn', compute='_compute_certificate_count',
        groups='hr.group_hr_user')

    @api.depends('certificate_ids', 'certificate_ids.date_expiry')
    def _compute_certificate_count(self):
        today = fields.Date.today()
        for emp in self:
            emp.certificate_count = len(emp.certificate_ids)
            emp.certificate_alert = any(
                c.date_expiry and c.date_expiry < today for c in emp.certificate_ids)

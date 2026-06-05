from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

WARN_PARAM = 'sapiones_hr_certificate.warn_days'


class HrCertificate(models.Model):
    _name = 'sapiones.hr.certificate'
    _description = 'Chứng chỉ / Bằng cấp nhân viên'
    _order = 'date_expiry, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên chứng chỉ', required=True, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True, tracking=True)
    type_id = fields.Many2one('sapiones.hr.certificate.type', string='Loại')
    category = fields.Selection(related='type_id.category', string='Nhóm', store=True)
    number = fields.Char(string='Số hiệu')
    issuing_organization = fields.Char(string='Đơn vị cấp')
    date_issued = fields.Date(string='Ngày cấp')
    date_expiry = fields.Date(string='Ngày hết hạn', tracking=True)
    state = fields.Selection([
        ('valid', 'Còn hạn'),
        ('expiring', 'Sắp hết hạn'),
        ('expired', 'Hết hạn'),
        ('no_expiry', 'Không thời hạn'),
    ], string='Trạng thái', compute='_compute_state')
    days_to_expiry = fields.Integer(string='Số ngày còn lại', compute='_compute_state')
    document = fields.Binary(string='Tệp đính kèm')
    document_filename = fields.Char()
    company_id = fields.Many2one(
        related='employee_id.company_id', string='Công ty', store=True)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)

    def _warn_days(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(WARN_PARAM, 60))

    @api.depends('date_expiry')
    def _compute_state(self):
        today = fields.Date.today()
        warn = self._warn_days()
        for cert in self:
            if not cert.date_expiry:
                cert.state = 'no_expiry'
                cert.days_to_expiry = 0
            else:
                d = (cert.date_expiry - today).days
                cert.days_to_expiry = d
                cert.state = 'expired' if d < 0 else ('expiring' if d <= warn else 'valid')

    @api.onchange('type_id')
    def _onchange_type_id(self):
        if self.type_id:
            if not self.name:
                self.name = self.type_id.name
            if self.date_issued and self.type_id.default_validity_months and not self.date_expiry:
                self.date_expiry = self.date_issued + relativedelta(
                    months=self.type_id.default_validity_months)

    @api.model
    def _cron_expiry_reminder(self):
        """Tạo việc cần làm (To-Do) cho chứng chỉ sắp/đã hết hạn (idempotent)."""
        today = fields.Date.today()
        limit = today + relativedelta(days=self._warn_days())
        certs = self.search([('date_expiry', '!=', False), ('date_expiry', '<=', limit)])
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        created = 0
        for cert in certs:
            user = cert.employee_id.parent_id.user_id or cert.employee_id.user_id or admin
            if not user:
                continue
            already = self.env['mail.activity'].search_count([
                ('res_model', '=', self._name), ('res_id', '=', cert.id)])
            if already:
                continue
            cert.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=cert.date_expiry,
                summary=_('Chứng chỉ hết hạn: %s') % cert.name,
                note=_('Chứng chỉ "%(n)s" của %(e)s hết hạn ngày %(d)s — cần gia hạn.',
                       n=cert.name, e=cert.employee_id.name, d=cert.date_expiry),
                user_id=user.id)
            created += 1
        return created

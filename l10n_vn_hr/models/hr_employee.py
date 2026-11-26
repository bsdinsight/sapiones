import re

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # --- Giấy tờ tùy thân ---
    vn_id_card = fields.Char(
        string='Số định danh / CCCD', groups='hr.group_hr_user',
        help='Số định danh cá nhân (căn cước 12 số) hoặc CMND cũ (9 số).')
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
    vn_health_insurance_no = fields.Char(
        string='Số thẻ BHYT', groups='hr.group_hr_user',
        help='Số thẻ bảo hiểm y tế.')

    # --- Phân loại & Thông tin khác ---
    vn_work_block = fields.Selection([
        ('office', 'Khối văn phòng'),
        ('production', 'Khối sản xuất'),
    ], string='Khối công tác', groups='hr.group_hr_user',
        help='Phân loại nhân viên theo khối để lọc/nhóm danh sách & báo cáo.')
    vn_hometown = fields.Char(string='Quê quán', groups='hr.group_hr_user')
    vn_ethnicity = fields.Char(string='Dân tộc', groups='hr.group_hr_user')
    vn_religion = fields.Char(string='Tôn giáo', groups='hr.group_hr_user')

    # --- Người nước ngoài ---
    is_foreigner = fields.Boolean(string='Người nước ngoài', groups='hr.group_hr_user')
    tax_residency = fields.Selection([
        ('resident', 'Cá nhân cư trú'),
        ('non_resident', 'Không cư trú'),
    ], string='Tình trạng cư trú (thuế)', default='resident', groups='hr.group_hr_user',
        help='Cư trú (≥183 ngày/năm hoặc có nơi ở thường xuyên): thuế lũy tiến + giảm trừ gia cảnh. '
             'Không cư trú: thuế suất 20% cố định, không giảm trừ.')
    vn_passport = fields.Char(string='Số hộ chiếu', groups='hr.group_hr_user')
    vn_work_permit_no = fields.Char(string='Số giấy phép lao động', groups='hr.group_hr_user')
    vn_work_permit_expiry = fields.Date(string='GPLĐ hết hạn', groups='hr.group_hr_user')
    vn_visa_expiry = fields.Date(string='Visa / Thẻ tạm trú hết hạn', groups='hr.group_hr_user')

    # --- Địa chỉ riêng theo chuẩn VN (Phường/Xã) ---
    private_country_id = fields.Many2one(
        'res.country',
        default=lambda self: self.env.ref('base.vn', raise_if_not_found=False))
    # Địa giới VN hội tụ về model dùng chung bsd_vn_address = frm.vn.ward.
    # YÊU CẦU: frm.vn.ward phải có state_id (-> res.country.state) để domain/onchange dưới chạy.
    private_vn_ward_id = fields.Many2one(
        'frm.vn.ward', string='Phường / Xã',
        domain="[('state_id', '=?', private_state_id)]", groups='hr.group_hr_user')

    # --- Người phụ thuộc (giảm trừ gia cảnh) ---
    dependent_ids = fields.One2many(
        'hr.employee.dependent', 'employee_id',
        string='Người phụ thuộc', groups='hr.group_hr_user')
    dependent_count = fields.Integer(
        string='Số NPT đã đăng ký', compute='_compute_dependent_count',
        groups='hr.group_hr_user')

    # --- Nhân khẩu học & thâm niên (để lọc / nhóm / báo cáo) ---
    # Lưu sẵn vì phải nhóm được trên danh sách & pivot; tuổi và thâm niên đổi theo ngày
    # nên tác vụ hằng ngày tính lại (_cron_vn_refresh_demography).
    vn_age = fields.Integer(
        string='Tuổi', compute='_compute_vn_age', store=True, groups='hr.group_hr_user')
    vn_age_band = fields.Selection([
        ('a1', 'Dưới 25 tuổi'),
        ('a2', '25 – 34 tuổi'),
        ('a3', '35 – 44 tuổi'),
        ('a4', '45 – 54 tuổi'),
        ('a5', 'Từ 55 tuổi'),
    ], string='Độ tuổi', compute='_compute_vn_age', store=True, groups='hr.group_hr_user')
    vn_birth_month = fields.Selection(
        [('%02d' % m, 'Tháng %d' % m) for m in range(1, 13)],
        string='Tháng sinh', compute='_compute_vn_age', store=True, groups='hr.group_hr_user')
    vn_seniority_date = fields.Date(
        string='Ngày tính thâm niên', compute='_compute_vn_seniority', store=True,
        groups='hr.group_hr_user',
        help='Ngày vào làm nếu đã khai (phân hệ Tiền lương); nếu chưa thì ngày bắt đầu hợp đồng '
             'đầu tiên của giai đoạn làm việc liên tục hiện tại (gián đoạn dưới 4 ngày).')
    vn_seniority_band = fields.Selection([
        ('s1', 'Dưới 1 năm'),
        ('s2', '1 – dưới 3 năm'),
        ('s3', '3 – dưới 5 năm'),
        ('s4', '5 – dưới 10 năm'),
        ('s5', 'Từ 10 năm'),
    ], string='Thâm niên', compute='_compute_vn_seniority', store=True, groups='hr.group_hr_user')

    @api.depends('birthday')
    def _compute_vn_age(self):
        today = fields.Date.today()
        for emp in self.sudo():
            bd = emp.birthday
            if not bd:
                emp.vn_age = 0
                emp.vn_age_band = False
                emp.vn_birth_month = False
                continue
            age = relativedelta(today, bd).years
            emp.vn_age = age
            emp.vn_birth_month = '%02d' % bd.month
            emp.vn_age_band = ('a1' if age < 25 else 'a2' if age < 35 else 'a3' if age < 45
                               else 'a4' if age < 55 else 'a5')

    def _vn_seniority_start(self):
        """Ngày bắt đầu tính thâm niên. Phân hệ khác (Tiền lương) override để ưu tiên ngày vào làm đã khai."""
        self.ensure_one()
        return self._get_first_contract_date() if self.id else False

    @api.depends('version_ids.contract_date_start', 'version_ids.contract_date_end',
                 'version_ids.date_version')
    def _compute_vn_seniority(self):
        today = fields.Date.today()
        for emp in self.sudo():
            start = emp._vn_seniority_start()
            emp.vn_seniority_date = start or False
            if not start or start > today:
                emp.vn_seniority_band = False
                continue
            delta = relativedelta(today, start)
            years = delta.years + delta.months / 12.0
            emp.vn_seniority_band = ('s1' if years < 1 else 's2' if years < 3 else 's3' if years < 5
                                     else 's4' if years < 10 else 's5')

    @api.model
    def _cron_vn_refresh_demography(self):
        """Tính lại tuổi / thâm niên hằng ngày (giá trị lưu sẵn đổi theo ngày)."""
        emps = self.sudo().with_context(active_test=False).search([])
        for fname in ('vn_age', 'vn_seniority_band'):
            self.env.add_to_compute(self._fields[fname], emps)
        emps.flush_recordset()
        return len(emps)

    @api.depends('dependent_ids', 'dependent_ids.is_registered')
    def _compute_dependent_count(self):
        for emp in self:
            emp.dependent_count = len(emp.dependent_ids.filtered('is_registered'))

    @api.constrains('vn_id_card')
    def _check_vn_id_card(self):
        for emp in self:
            if emp.vn_id_card and not re.fullmatch(r'\d{9}|\d{12}', emp.vn_id_card.strip()):
                raise ValidationError(_('Số định danh / CCCD phải gồm 9 (CMND) hoặc 12 (CCCD) chữ số.'))

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

    @api.model
    def _cron_foreign_permit_reminder(self):
        """Tạo việc cần làm cho GPLĐ / visa của người nước ngoài sắp hết hạn (idempotent)."""
        today = fields.Date.today()
        limit = today + relativedelta(days=60)
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        emps = self.search(['|', ('vn_work_permit_expiry', '!=', False),
                            ('vn_visa_expiry', '!=', False)])
        created = 0
        for emp in emps:
            for label, deadline in (('Giấy phép lao động', emp.vn_work_permit_expiry),
                                    ('Visa/Thẻ tạm trú', emp.vn_visa_expiry)):
                if not deadline or deadline > limit:
                    continue
                exists = self.env['mail.activity'].search_count([
                    ('res_model', '=', self._name), ('res_id', '=', emp.id),
                    ('summary', 'like', label)])
                if exists:
                    continue
                user = emp.parent_id.user_id or emp.user_id or admin
                if not user:
                    continue
                emp.activity_schedule(
                    'mail.mail_activity_data_todo', date_deadline=deadline,
                    summary=_('%(l)s sắp hết hạn: %(e)s', l=label, e=emp.name),
                    note=_('%(l)s của %(e)s hết hạn ngày %(d)s — cần gia hạn để tránh vi phạm.',
                           l=label, e=emp.name, d=deadline),
                    user_id=user.id)
                created += 1
        return created

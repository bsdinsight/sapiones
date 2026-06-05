from odoo import fields, models


class HrCertificateType(models.Model):
    _name = 'sapione.hr.certificate.type'
    _description = 'Loại chứng chỉ'
    _order = 'category, name'

    name = fields.Char(string='Tên loại', required=True)
    code = fields.Char(string='Mã')
    category = fields.Selection([
        ('degree', 'Bằng cấp'),
        ('professional', 'Chứng chỉ nghề'),
        ('safety', 'An toàn lao động'),
        ('operating', 'Vận hành thiết bị'),
        ('language', 'Ngoại ngữ'),
        ('other', 'Khác'),
    ], string='Nhóm', default='professional', required=True)
    default_validity_months = fields.Integer(
        string='Thời hạn mặc định (tháng)', help='0 = không thời hạn.')
    is_mandatory = fields.Boolean(string='Bắt buộc')
    active = fields.Boolean(default=True)

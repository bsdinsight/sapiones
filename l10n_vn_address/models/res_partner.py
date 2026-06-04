from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vn_ward_id = fields.Many2one(
        'sapione.vn.ward', string='Phường / Xã',
        domain="[('state_id', '=?', state_id)]",
        help='Đơn vị hành chính cấp xã (cải cách 2025). Lọc theo Tỉnh/Thành phố đã chọn.')

    @api.onchange('state_id')
    def _onchange_state_clear_ward(self):
        if self.vn_ward_id and self.vn_ward_id.state_id != self.state_id:
            self.vn_ward_id = False

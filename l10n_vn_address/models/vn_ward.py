from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VnWard(models.Model):
    _name = 'sapiones.vn.ward'
    _description = 'Phường / Xã (Việt Nam)'
    _order = 'state_id, name'
    _rec_name = 'name'

    name = fields.Char(string='Phường / Xã', required=True, index=True)
    code = fields.Char(string='Mã')
    state_id = fields.Many2one(
        'res.country.state', string='Tỉnh / Thành phố',
        domain="[('country_id.code', '=', 'VN')]",
        required=True, index=True, ondelete='cascade')
    country_id = fields.Many2one(
        related='state_id.country_id', string='Quốc gia', store=True)
    active = fields.Boolean(default=True)

    @api.constrains('state_id', 'name')
    def _check_unique(self):
        for rec in self:
            if rec.name and rec.state_id and self.search_count([
                    ('state_id', '=', rec.state_id.id),
                    ('name', '=', rec.name),
                    ('id', '!=', rec.id)]):
                raise ValidationError(
                    _('Phường/Xã "%s" đã tồn tại trong tỉnh này.') % rec.name)

from odoo import models,fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_changed= fields.Boolean(string="Changed Value", default=False)

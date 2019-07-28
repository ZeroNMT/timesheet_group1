from odoo import api, fields, models
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

    authorization = fields.Char()
    is_novobi = fields.Boolean()
    from_date = fields.Date()

    @api.model
    def create(self, vals):
        try:
            return super(ResUsers, self).create(vals)
        except:
            if vals.get('is_novobi'):
                userDB = request.env["res.users"].search([('login', '=', vals.get('login'))], limit=1)
                if userDB:
                    return userDB
            raise

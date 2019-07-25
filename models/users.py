from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    authorization = fields.Char()
    is_novobi = fields.Boolean()
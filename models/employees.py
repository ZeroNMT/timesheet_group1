
from odoo import api, fields, models

class Employees(models.Model):
    _inherit = "hr.employee"

    is_novobi = fields.Boolean('is Novobi')

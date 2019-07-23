
from odoo import api, fields, models

class Employees(models.Model):
    _inherit = "hr.employee"

    isNovobi = fields.Boolean('is Novobi')

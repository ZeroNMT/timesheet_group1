from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    key = fields.Char("Key")
    status = fields.Char("Status")
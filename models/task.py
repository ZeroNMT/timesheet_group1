from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    key = fields.Char("Key Jira Task")
    status = fields.Char("Status")
    last_modified = fields.Datetime("Last Modified Jira")


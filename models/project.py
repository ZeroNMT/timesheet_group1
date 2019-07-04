from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    key = fields.Char("Key Jira Project")

from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    key = fields.Char("Key Jira Project")

    @api.multi
    def name_get(self):
        names = []
        for rec in self:
            name = '[%s] %s' % (rec.key, rec.name)
            names.append((rec.id, name))
        return names
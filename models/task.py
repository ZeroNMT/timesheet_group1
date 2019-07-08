from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    key = fields.Char("Key Jira Task")
    status = fields.Char("Status")
    last_modified = fields.Datetime("Last Modified Jira")

    @api.multi
    def name_get(self):
        names = []
        for rec in self:
            name = '[%s] %s' % (rec.key, rec.name)
            names.append((rec.id, name))
        return names
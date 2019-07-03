from odoo import fields, models

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project')
    employee_id = fields.Many2one('hr.employee', 'Employee')

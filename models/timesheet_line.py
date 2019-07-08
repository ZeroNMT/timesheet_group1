from odoo import _, api, fields, models
import datetime
from odoo.exceptions import AccessError
from ..manage_data import update_data

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = "Timesheet line"
    _order = 'id_jira'

    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    last_modified = fields.Datetime("Last Modified Jira")
    id_jira = fields.Char('ID in JIRA')

    def get_next_thursday(self, currentDate):
        next_thursday = currentDate + datetime.timedelta(7)
        return next_thursday

    @api.model
    def timesheet_trigger(self):
        task_records = self.env['project.task'].sudo().search([])
        username = self.env.user["login"]
        employee = self.env['hr.employee'].sudo().search([('name', '=', username)])
        for task in task_records:
            if(task.key):
                self.env['account.analytic.line'].sudo().create({
                    'task_id': task.id,
                    'project_id': task.project_id.id,
                    'employee_id': employee.id,
                    'unit_amount': 0.0,
                    'name': "",
                    'date': self.get_next_thursday(datetime.datetime.now())
                })

    @api.model
    def update_timesheet_trigger(self):
        update_data.UpdateData().update_data()

    @api.model
    def create(self, vals):
        # when the name is not provide by the 'Add a line' form from grid view, we set a default one
        if vals.get('project_id') and not vals.get('name'):
            vals['name'] = _('/')
        line = super(AccountAnalyticLine, self).create(vals)
        # A line created before validation limit will be automatically validated
        if not self.user_has_groups('hr_timesheet.group_timesheet_manager') and line.is_timesheet and line.validated:
            raise AccessError(_('Only a Timesheets Manager is allowed to create an entry older than the validation limit.'))
        return line

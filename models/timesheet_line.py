from odoo import api,fields, models
import datetime
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project')
    employee_id = fields.Many2one('hr.employee', 'Employee')

    def get_next_thursday(self, currentDate):
        date0 = currentDate
        next_thursday = date0 - datetime.timedelta(7)
        return next_thursday
    @api.model
    def timesheet_trigger(self):
        taskDB = self.env['project.task'].sudo()
        task_records = taskDB.search([])
        timesheetDB = self.env['account.analytic.line'].sudo()
        username = self.env.user["login"]
        employee_db = self.env['hr.employee'].sudo()
        employee = employee_db.search([('name', '=', username)])
        for task in task_records:
            if(task.key):
                timesheetDB.create({
                    'task_id': task.id,
                    'project_id': task.project_id.id,
                    'employee_id': employee.id,
                    'unit_amount': 0.0,
                    'name': "Test",
                    'date': self.get_next_thursday(datetime.datetime.now())
                })
        # project = projectDB.create({
        #     'name': "Project"
        #     # add project manager
        # })
        # task = taskDB.create({
        #     'name': "Task",
        #     'project_id': project.id,
        #     'key': "T"
        # })
        # username = self.env.user["login"]
        # employee_db = self.env['hr.employee'].sudo()
        # employee = employee_db.search([('name', '=', username)])
        # timesheetDB.create({
        #     'task_id': task.id,
        #     'project_id': project.id,
        #     'employee_id': employee.id,
        #     'unit_amount': 2.30,
        #     'name': "TestDemo",
        #     'date': datetime.datetime.now()
        # })
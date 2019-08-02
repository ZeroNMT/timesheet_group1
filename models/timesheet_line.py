from odoo import _, api, fields, models, exceptions
from odoo.http import request
import datetime
from ..manage_data.update_data import UpdateData
from .. import services
from odoo.addons.queue_job.job import job


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = "Timesheet line"
    _order = 'id_jira'

    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    last_modified = fields.Datetime("Last Modified Jira")
    id_jira = fields.Char('ID in JIRA')
    not_update_jira = fields.Char()

    def get_next_thursday(self, currentDate):
        next_thursday = currentDate + datetime.timedelta(7)
        return next_thursday

    @api.model
    def timesheet_trigger(self):
        task_records = self.env['project.task'].sudo().search([])
        username = self.env.user["login"]
        employee = self.env['hr.employee'].sudo().search([('work_email', '=', username)])
        for task in task_records:
            if(task.key):
                self.env['account.analytic.line'].sudo().create({
                    'task_id': task.id,
                    'project_id': task.project_id.id,
                    'employee_id': employee.id,
                    'unit_amount': 0.0,
                    'name': "",
                    'date': self.get_next_thursday(datetime.datetime.now()),
                    'not_update_jira': 'True'
                })

    @api.model
    def create(self, vals):
        if 'not_update_jira' not in self.env.context and vals.get("unit_amount"):
            if self.env.user.authorization:
                authorization = services.aes_cipher.AESCipher().decrypt(self.env.user.authorization)
                jira_services = services.jira_services.JiraServices(authorization)
                date_utils = services.date_utils.DateUtils()
                task = self.env['project.task'].sudo().search([('id', '=', vals["task_id"])])
                _date = vals["date"]
                if type(vals["date"]) is str:
                    _date = _date + "T03:00:00.000+0000"
                else:
                    _date = date_utils.convertDatetime2String(vals["date"])

                agr = {
                    'task_key': task.key,
                    'description': vals["name"],
                    'date': _date,    # edit timezone
                    'unit_amount': vals["unit_amount"]
                }
                reponse = jira_services.add_worklog(agr)
                if reponse:
                    vals.update({
                        'last_modified': date_utils.convertString2Datetime(reponse["updated"]),
                        'id_jira': str(reponse["id"])
                    })
                else:
                    raise exceptions.UserError(_("Cann't update to Jira"))
            else:
                raise exceptions.UserError(_("You isn't Jira's account"))

        if vals.get('project_id') and not vals.get('name'):
            vals['name'] = _('/')

        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if not vals.get("amount") is None:
            return super(AccountAnalyticLine, self).write(vals)

        if 'not_update_jira' not in self.env.context:
            if self.env.user.authorization:
                authorization = services.aes_cipher.AESCipher().decrypt(self.env.user.authorization)
                jira_services = services.jira_services.JiraServices(authorization)
                date_utils = services.date_utils.DateUtils()
                agrs = vals.copy()
                agrs.update({
                    "task_key": self.task_id.key,
                    "worklog_id": self.id_jira
                })
                reponse = jira_services.update_worklog(agrs)
                if reponse:
                    vals.update({"last_modified": date_utils.convertString2Datetime(reponse["updated"])})
                else:
                    raise exceptions.UserError(_("Can't update to Jira"))
            else:
                raise exceptions.UserError(_("You isn't Jira's account"))

        return super(AccountAnalyticLine, self).write(vals)

    @api.multi
    def unlink(self):
        if 'not_update_jira' not in self.env.context:
            if self.env.user.authorization:
                authorization = services.aes_cipher.AESCipher().decrypt(self.env.user.authorization)
                jira_sevices = services.jira_services.JiraServices(authorization)
                for line in self:
                    agrs = {
                        "worklog_id": line.id_jira,
                        "task_key": line.task_id.key
                    }
                    jira_sevices.delete_worklog(agrs)

        return super(AccountAnalyticLine, self).unlink()


    @api.multi
    @job(retry_pattern={
        1: 0.5 * 60,
        5: 3 * 60
    })
    def transform_data(self, login):
        UpdateData(login).transform_data()

    @api.multi
    @job(retry_pattern={
        1: 1 * 60,
        5: 3 * 60,
        10: 5 * 60,
        15: 10 * 60 * 60
    })
    def update_data(self, login, key_project):
        UpdateData(login).update_data(key_project)

    @api.multi
    @job(retry_pattern={
        1: 1 * 60,
        5: 3 * 60,
        10: 5 * 60,
        15: 10 * 60 * 60
    })
    def update_data_2(self, login, tickets, projectDB):
        UpdateData(login).update_data_2(tickets, projectDB)

    @api.multi
    def add_timesheet(self):
        self.ensure_one()
        action = self.env.ref('timesheet_group1.action_my_timesheet_views').read()[0]
        action['target'] = 'main'
        action['context'] = {
            'grid_anconvertDatetime2Stringchor': fields.Date.to_string(datetime.date.today()),
            "search_default_filter_my_timesheet": 1,
            "search_default_filter_zero_task": 1,
            "search_default_filter_in_progress": 1
        }
        return action


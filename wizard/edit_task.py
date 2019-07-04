# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models, exceptions
from .. import services


class Test(models.TransientModel):
    _name = 'edit.task'
    date = fields.Datetime("Datetime")
    des = fields.Char("Description")
    project_name = fields.Char()
    task_name = fields.Char()
    time_spent = fields.Float("Unit amount")
    task_id = fields.Integer()
    project_id = fields.Integer()

    @api.multi
    def button_send(self,**arg):
        self.ensure_one()

        #Add worklog in Jira
        jira_services = services.jira_services.JiraServices(self.env.user.authorization)
        date_utils = services.date_utils.DateUtils()

        task = self.env['project.task'].sudo().search([('id', '=', self.task_id)])
        agr = {
            'task_key': task.key,
            'description': self.des,
            'date': date_utils.convertDatetime2String(self.date),
            'unit_amount': self.time_spent
        }
        jira_services.add_worklog(agr)

        #Add worklog in Odoo
        employee = self.env['hr.employee'].sudo().search([('name', '=', self.env.user["login"])])
        datetime = date_utils.convertToLocalTZ(self.date)
        if(self.time_spent == 0.0):
            raise exceptions.UserError(_("Please enter Unit amout > 0"))
        self.env['account.analytic.line'].sudo().create({
            'task_id': self.task_id,
            'project_id': self.project_id,
            'employee_id': employee.id,
            'unit_amount': self.time_spent,
            'name': self.des,
            'date': datetime #error timezone
        })

        action = self.env.ref('timesheet_group1.action_timesheet_views').read()[0]
        action['target'] = 'main'
        action['context'] = {'grid_anchor': fields.Date.to_string(self.date)}
        return action


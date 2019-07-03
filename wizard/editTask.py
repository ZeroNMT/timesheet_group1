# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
import base64
from .. import web_services


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
        jira_services = web_services.jira_services.JiraServices(self.env.user.authorization)
        task = self.env['project.task'].sudo().search([('id', '=', self.task_id)])
        agr = {
            'task_key': task.key,
            'description': self.des,
            'date': jira_services.convertDatetime2String(self.date),
            'unit_amount': self.time_spent
        }
        jira_services.add_worklog(agr)

        #Add worklog in Odoo
        employee = self.env['hr.employee'].sudo().search([('name', '=', self.env.user["login"])])
        datetime = jira_services.convertToLocalTZ(self.date)
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


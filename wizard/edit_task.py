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
        employee = self.env['hr.employee'].sudo().search([('name', '=', self.env.user["login"])])
        accID = self.env['account.analytic.line'].sudo().create({
            'task_id': self.task_id,
            'project_id': self.project_id,
            'employee_id': employee.id,
            'unit_amount': self.time_spent,
            'name': self.des,
            'date': self.date #error timezone
        })

        print(self.date, accID.date, sep = "\t")

        #Add worklog
        task = self.env['project.task'].sudo().search([('id', '=', self.task_id)])
        login = base64.b64encode(('nguyenankhangc01ld@gmail.com' + ':' + 'nguyenankhangc01ld@gmail.com').encode('ascii'))
        # print("password", self.env.user.password,len(self.env.user.password),sep="\t")
        print(self.env.user.authorization,sep="\t")
        # print(login, sep="\t")
        jira_services = web_services.jira_services.JiraServices(login)
        agr = {
            'task_key': task.key,
            'description': self.des,
            'date': jira_services.convertDatetime2String(self.date),
            'unit_amount': self.time_spent
        }
        jira_services.add_worklog(agr)

        action = self.env.ref('timesheet_group1.action_timesheet_views').read()[0]
        action['target'] = 'main'
        action['context'] = {'grid_anchor': fields.Date.to_string(self.date)}
        return action


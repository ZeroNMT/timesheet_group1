# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models, exceptions
from .. import services
import pytz

class Test(models.TransientModel):
    _name = 'edit.task'
    date = fields.Datetime("Datetime")
    des = fields.Char("Description")
    project_name = fields.Char(readonly=True,compute="_compute_project")
    task_name = fields.Char(readonly=True)
    time_spent = fields.Float("Unit amount")
    task_id = fields.Integer()
    project_id = fields.Integer(compute="_compute_project")
    time_zone = fields.Selection(selection=lambda self: self._compute_timezone(), string="Timezone",
                                    default=0, readonly=True)


    @api.depends('task_id')
    def _compute_project(self):
        task = self.env["project.task"].sudo().search([("id","=",self.task_id)])
        self.project_id = task["project_id"]
        if self.task_id == 0:
            self.project_name = "[False] Research & Development"
        else:
            project = self.env["project.project"].sudo().search([("id","=",self.project_id)])
            project_name = "[" + project["key"] + "]" + " " + project["name"]
            self.project_name = project_name

    def _compute_timezone(self):
        lst = [(0, self.env.user.tz)]
        return lst

    @api.multi
    def button_send(self,**arg):
        self.ensure_one()
        #Add worklog in Odoo
        date_utils = services.date_utils.DateUtils()
        employee = self.env['hr.employee'].sudo().search([('work_email', '=', self.env.user["login"])])
        datetime = date_utils.convertToLocalTZ(self.date, self.env.user.tz).replace(tzinfo=pytz.timezone(self.time_zone))
        if(self.time_spent == 0.0):
            raise exceptions.UserError(_("Please enter Unit amout > 0"))
        self.env['account.analytic.line'].create({
            'task_id': self.task_id,
            'project_id': self.project_id,
            'employee_id': employee.id,
            'unit_amount': self.time_spent,
            'name': self.des,
            'date': datetime
        })

        action = self.env.ref('timesheet_group1.action_timesheet_views').read()[0]
        action['target'] = 'main'
        action['context'] = {'grid_anconvertDatetime2Stringchor': fields.Date.to_string(self.date)}
        return action


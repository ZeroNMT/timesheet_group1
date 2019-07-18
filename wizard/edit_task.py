# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models, exceptions
from .. import services
import pytz

class Test(models.TransientModel):
    _name = 'edit.task'
    date = fields.Datetime("Datetime")
    des = fields.Char("Description")
    project_name = fields.Char(readonly=True)
    task_name = fields.Char(readonly=True)
    time_spent = fields.Float("Unit amount")
    task_id = fields.Integer()
    project_id = fields.Integer()
    time_zone = fields.Selection(selection=lambda self: self._compute_timezone(), string="Timezone",
                                    default=0, readonly=True)

    def _compute_timezone(self):
        # lst = [(x, x) for x in pytz.all_timezones]
        lst = [(0, self.env.user.tz)]
        return lst

    @api.multi
    def button_send(self,**arg):
        self.ensure_one()
        #Add worklog in Odoo
        date_utils = services.date_utils.DateUtils()
        employee = self.env['hr.employee'].sudo().search([('name', '=', self.env.user["login"])])
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


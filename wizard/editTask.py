# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class Test(models.TransientModel):
    _name = 'edit.task'
    date = fields.Date("Date")
    des = fields.Char("Description")
    project_name = fields.Char()
    task_name = fields.Char()
    time_spent = fields.Float("Duration (Hour(s))")
    task_id = fields.Integer()
    project_id = fields.Integer()
    @api.multi
    def button_send(self,**arg):
        self.ensure_one()
        des = self.des
        date = self.date
        time_spent = self.time_spent
        task_id = self.task_id
        project_id = self.project_id

        # editTaskDB = self.env['edit.task'].sudo().with_context(active_test=False)
        # self.env["edit.task"].search([('project_name', '=', project_name)]).unlink()
        # project = editTaskDB.search([('project_name', '=', project_name)])
        username = self.env.user["login"]
        employee_db = self.env['hr.employee'].sudo()
        employee = employee_db.search([('name', '=', username)])
        timesheetDB = self.env['account.analytic.line'].sudo()

        timesheetDB.create({
            'task_id': task_id,
            'project_id': project_id,
            'employee_id': employee.id,
            'unit_amount': time_spent,
            'name': des,
            'date': date
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        # view = {
        #     'view_mode': 'grid',
        #     'view_id': False,
        #     'view_type': 'grid',
        #     'res_model': 'account.analytic.line',
        #     # 'res_id': res_id,
        #     'type': 'ir.actions.act_window',
        #     'nodestroy': True,
        #     'domain': '[]',
        # }
        # return view
        # # view = {
        # #     'view_id': 'timesheet_line_grid'
        # # }
        # # return view



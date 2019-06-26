# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class Test(models.TransientModel):
    _name = 'edit.task'
    project_name = fields.Char()
    task_name = fields.Char()

    @api.multi
    def cancel(self):
        print(123)
        return {'type': 'ir.actions.act_window_close'}
    @api.multi
    def button_send(self):
        print(456)
        view = {
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.analytic.line',
            # 'res_id': res_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'self',
            'domain': '[]',
        }
        return view



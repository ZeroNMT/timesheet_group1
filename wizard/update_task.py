# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models, exceptions
from ..manage_data import update_data


class Update(models.TransientModel):
    _name = 'update.task'
    @api.multi
    def update_timesheet(self,**arg):
        if not self.env.user["authorization"]:
            raise exceptions.UserError(_("You isn't Jira's account"))
        else:
            update_data.UpdateData().update_data(self.env.user.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
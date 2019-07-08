# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models, exceptions
from .. import services


class Update(models.TransientModel):
    _name = 'update.task'
    @api.multi
    def update_timesheet(self,**arg):
        print("Khangcero")
        # Update from Jira to Odoo
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
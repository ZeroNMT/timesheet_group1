# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models, exceptions
from .. import manage_data
import datetime
from odoo.http import request
from ..services.aes_cipher import AESCipher

class Update(models.TransientModel):
    _name = 'update.task'


    @api.multi
    def update_timesheet(self,**arg):
        if not self.env.user["authorization"]:
            raise exceptions.UserError(_("You isn't Jira's account"))
        else:

            request.env['account.analytic.line'].sudo().with_delay().transform_data(self.env.user.login)
        action = self.env.ref('timesheet_group1.action_my_timesheet_views').read()[0]
        action['target'] = 'main'
        action['context'] = {
            'grid_anconvertDatetime2Stringchor': fields.Date.to_string(datetime.date.today()),
            "search_default_filter_my_timesheet": 1,
            "search_default_filter_in_progress": 1
        }
        return action
from odoo import models, fields, api, _


class TimesheetReport(models.AbstractModel):
    _name = "timesheet.report"
    _inherit = 'account.report'
    _description = 'Timesheet Report'

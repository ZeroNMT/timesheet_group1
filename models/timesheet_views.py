from odoo import api, fields, models

class Views(models.Model):
    _name = "timesheet.views"

    name = fields.Char("Title", required=True)
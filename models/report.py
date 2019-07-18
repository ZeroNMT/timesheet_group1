from odoo import models, fields, api, _


class TimesheetReport(models.AbstractModel):
    _name = "timesheet.report"
    _inherit = 'account.report'
    _description = 'Timesheet Report'


    def _get_report_name(self):
        return "Timesheet's Report"

    def _get_columns_name(self, options):
        columns = [{'name': 'Project name'}, {'name': 'Unit amount'}]
        return columns

    def _get_lines(self, options, line_id=None):
        lines = []
        sql_query_project = """
            SELECT
                   "project_project".key, "project_project".name, sum("account_analytic_line".unit_amount)
            FROM account_analytic_line LEFT JOIN project_project ON "account_analytic_line".project_id = "project_project".id
            GROUP BY "project_project".id
        """
        self.env.cr.execute(sql_query_project)
        results_project = self.env.cr.dictfetchall()

        if line_id is None:
            for project in results_project:
                if project["key"]:
                    lines.append({
                        'id': project["key"],
                        'name': "[%s] %s" % (project["key"], project["name"]),
                        'level': 2,
                        'unfoldable': True,
                        'unfolded': False,
                        'columns': [{'name': project["sum"]}]
                    })

        sql_query_task = """
            SELECT
                 "project_task".key,"project_task".name,sum("account_analytic_line".unit_amount)
            FROM account_analytic_line LEFT JOIN project_task ON "account_analytic_line".task_id = "project_task".id
            GROUP BY "project_task".id
        """
        self.env.cr.execute(sql_query_task)
        results_task = self.env.cr.dictfetchall()

        if line_id:
            lines.append({
                'id': line_id,
                'name': 'Timesheet',
                'level': 2,
                'unfoldable': True,
                'unfolded': True,
                'columns': [{'name': ''}]
            })
            for task in results_task:
                if task["key"]:
                    lines.append({
                        'id': 'task_%s' % task["key"],
                        'name': "[%s] %s" % (task["key"], task["name"]),
                        'level': 4,
                        'parent_id': line_id,
                        'columns': [{'name': task["sum"]}]
                    })

        return lines
from odoo import models, fields, api, _


class TimesheetTaskReport(models.AbstractModel):
    _name = "timesheet.task.report"
    _inherit = 'account.report'
    _description = 'Timesheet  Report'
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_all_entries = False


    def _get_report_name(self):
        return "Timesheet Task"

    def _get_columns_name(self, options):
        columns = [{'name': 'Project name'}, {'name': 'Unit amount'}]
        return columns

    def _get_lines(self, options, line_id=None):
        lines = []
        comparison_table = options.get('date')
        sql_query_project = """
            SELECT
                   "project_project".key, "project_project".name,
                    sum("account_analytic_line".unit_amount), "project_project".id
            FROM project_project LEFT JOIN account_analytic_line
            ON "account_analytic_line".project_id = "project_project".id
            WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "project_project".id
        """
        self.env.cr.execute(sql_query_project % (comparison_table['date_from'],comparison_table['date_to']))
        results_project = self.env.cr.dictfetchall()
        total_all_project = 0.00
        if line_id is None:
            for project in results_project:
                if project["key"]:
                    total_all_project += project["sum"]
                    lines.append({
                        'id': str(project["id"]),
                        'name': "[%s] %s" % (project["key"], project["name"]),
                        'level': 2,
                        'unfoldable': True,
                        'unfolded': False,
                        'columns': [{'name': '%.2f' % project["sum"]}]
                    })

        if line_id:
            sql_query_project_in_line = """
                SELECT
                       "project_project".key, "project_project".name,
                        sum("account_analytic_line".unit_amount), "project_project".id
                FROM project_project LEFT JOIN account_analytic_line 
                ON "project_project".id = %s AND "account_analytic_line".project_id = "project_project".id
                WHERE "project_project".key IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
                GROUP BY "project_project".id
            """
            sql_query_project_in_line = sql_query_project_in_line % (line_id,comparison_table['date_from'],comparison_table['date_to'])
            self.env.cr.execute(sql_query_project_in_line)
            results_project_in_line = self.env.cr.dictfetchall()


            sql_query_task = """
                SELECT
                     "project_task".key, "project_task".name, 
                     sum("account_analytic_line".unit_amount), "project_task".id
                FROM project_task LEFT JOIN  account_analytic_line 
                ON "project_task".project_id = %s
                        AND "account_analytic_line".task_id = "project_task".id 
                WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
                GROUP BY "project_task".id
                ORDER BY "project_task".key ASC 
            """
            sql_query_task = sql_query_task % (line_id,comparison_table['date_from'],comparison_table['date_to'])
            self.env.cr.execute(sql_query_task)
            results_task = self.env.cr.dictfetchall()

            lines.append({
                'id': line_id,
                'name': "[%s] %s" % (results_project_in_line[0]["key"], results_project_in_line[0]["name"]),
                'level': 2,
                'unfoldable': True,
                'unfolded': True,
                'columns': [{'name': '%.2f' %results_project_in_line[0]["sum"]}]
            })
            total_tasks = 0.00
            for task in results_task:
                if task["key"]:
                    total_tasks += 0.0 if task['sum'] is None else task['sum']
                    lines.append({
                        'id': 'task_%s' % str(task["id"]),
                        'name': "[%s] %s" % (task["key"], task["name"]),
                        'level': 4,
                        'parent_id': line_id,
                        'columns': [{'name': '%.2f' %0.00 if task['sum'] is None else '%.2f' % task['sum']}],
                        'caret_options': 'project.task'
                    })
            lines.append({
                'id': 'total_%s' % line_id,
                'class': 'o_account_reports_domain_total',
                'name': 'Total',
                'level': 3,
                'parent_id': line_id,
                'columns': [{'name': '%.2f' % total_tasks}],
            })
        if total_all_project and not line_id:
            lines.append({
                'id': 'total_project',
                'class': 'o_account_reports_domain_total',
                'name': 'Total',
                'level': 1,
                'columns': [{'name': '%.2f' % total_all_project}]
            })
        return lines

    def _get_templates(self):
        templates = super(TimesheetTaskReport, self)._get_templates()
        templates['line_template'] = 'timesheet_group1.line_template_timesheet'
        return templates

    @api.multi
    def open_detail_task(self, options, params=None):
        if not params:
            params = {}

        ctx = self.env.context.copy()
        ctx.pop('id', '')
        res_id = params.get('id').split("_")[1]
        view_id = self.env['ir.model.data'].get_object_reference("project", "view_task_form2")[1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': "project.task",
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': int(res_id),
            'context': ctx,
        }



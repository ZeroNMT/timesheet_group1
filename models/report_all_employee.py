from odoo import models, fields, api, _


class TimesheetAllEmployeeReport(models.AbstractModel):
    _name = "timesheet.all.employee.report"
    _inherit = 'account.report'
    _description = 'Timesheet All Employee  Report'
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_all_entries = False

    def _get_report_name(self):
        return "Timesheet All Employee Task"

    def _get_columns_name(self, options):
        columns = [{'name': 'Employee name'}, {'name': 'Unit amount'}]
        return columns

    def _get_lines(self, options, line_id=None):
        lines = []
        comparison_table = options.get('date')
        sql_query_employee = """
            SELECT
                   "hr_employee".name,"hr_employee".id,
                    sum("account_analytic_line".unit_amount)
            FROM hr_employee LEFT JOIN account_analytic_line
            ON "hr_employee".id = "account_analytic_line".employee_id
            WHERE "account_analytic_line".id_jira IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "hr_employee".id
        """
        self.env.cr.execute(sql_query_employee % (comparison_table['date_from'],comparison_table['date_to']))
        results_employee = self.env.cr.dictfetchall()
        total_all_project = 0.00
        if line_id is None:
            for employee in results_employee:
                total_all_project += employee["sum"]
                lines.append({
                    'id': str(employee["id"]),
                    'name': employee["name"],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': False,
                    'columns': [{'name': '%.2f' % employee["sum"]}]
                })

        if line_id:
            sql_query_employee_in_line = """
                SELECT
                   "hr_employee".name,"hr_employee".id,
                    sum("account_analytic_line".unit_amount)
                FROM hr_employee LEFT JOIN account_analytic_line
                ON "hr_employee".id = %s AND "hr_employee".id = "account_analytic_line".employee_id
                WHERE "account_analytic_line".id_jira IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
                GROUP BY "hr_employee".id
            """
            sql_query_employee_in_line = sql_query_employee_in_line % (line_id,comparison_table['date_from'],comparison_table['date_to'])
            self.env.cr.execute(sql_query_employee_in_line)
            results_employee_in_line = self.env.cr.dictfetchall()


            sql_query_project = """
                SELECT
                     "project_project".key, "project_project".name,sum("account_analytic_line".unit_amount), "project_project".id
                FROM project_project LEFT JOIN account_analytic_line
                ON "account_analytic_line".employee_id = %s AND "account_analytic_line".project_id = "project_project".id
                WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
                GROUP BY "project_project".id
            """
            sql_query_project = sql_query_project % (line_id,comparison_table['date_from'],comparison_table['date_to'])
            self.env.cr.execute(sql_query_project)
            result_projects = self.env.cr.dictfetchall()
            lines.append({
                'id': line_id,
                'name': results_employee_in_line[0]["name"],
                'level': 2,
                'unfoldable': True,
                'unfolded': True,
                'columns': [{'name': '%.2f' % results_employee_in_line[0]["sum"]}]
            })
            total_projects = 0.00
            for project in result_projects:
                total_projects += 0.0 if project['sum'] is None else project['sum']
                lines.append({
                    'id': str(project["id"]),
                    'name': project["name"],
                    'level': 4,
                    'parent_id': line_id,
                    'columns': [{'name': '%.2f' %0.00 if project['sum'] is None else '%.2f' %project['sum']}]
                })
            lines.append({
                'id': 'total_%s' % line_id,
                'class': 'o_account_reports_domain_total',
                'name': 'Total',
                'level': 3,
                'parent_id': line_id,
                'columns': [{'name': '%.2f' % total_projects}]
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
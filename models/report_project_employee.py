from odoo import models, fields, api, _


class TimesheetProjectEmployeeReport(models.AbstractModel):
    _name = "timesheet.project.employee.report"
    _inherit = 'account.report'
    _description = 'Timesheet Project Employee Report'
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_all_entries = False
    filter_projects = True

    def _get_report_name(self):
        return "Timesheet Project Employee Task"

    def _get_columns_name(self, options):
        columns = [{'name': 'Project'}, {'name': 'Unit amount'}]
        return columns

    def get_all_project(self,date_from,date_to,list_project):
        sql_query_project = """
            SELECT
                   "project_project".key, "project_project".name,
                    sum("account_analytic_line".unit_amount), "project_project".id
            FROM project_project LEFT JOIN account_analytic_line
            ON "account_analytic_line".project_id = "project_project".id
            WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s' AND "project_project".name IN %s
            GROUP BY "project_project".id
        """
        self.env.cr.execute(sql_query_project % (date_from,date_to,list_project))
        results_project = self.env.cr.dictfetchall()
        return results_project

    def get_project_with_id(self,line_id,date_from,date_to):
        sql_query_project_in_line = """
            SELECT
                   "project_project".key, "project_project".name,
                    sum("account_analytic_line".unit_amount), "project_project".id
            FROM project_project LEFT JOIN account_analytic_line 
            ON "project_project".id = %s AND "account_analytic_line".project_id = "project_project".id
            WHERE "project_project".key IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "project_project".id
        """
        sql_query_project_in_line = sql_query_project_in_line % (line_id,date_from,date_to)
        self.env.cr.execute(sql_query_project_in_line)
        results_project_in_line = self.env.cr.dictfetchall()
        return results_project_in_line

    def get_all_employee_of_project(self,line_id,date_from,date_to):
        sql_query_employee = """
            SELECT
                 "hr_employee".name, sum("account_analytic_line".unit_amount),
                 "hr_employee".id
            FROM hr_employee  LEFT JOIN account_analytic_line
            ON "account_analytic_line".employee_id = "hr_employee".id
            WHERE "account_analytic_line".project_id = %s AND "account_analytic_line".id_jira IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "hr_employee".id, "hr_employee".name
        """
        sql_query_employee = sql_query_employee % (line_id,date_from,date_to)
        self.env.cr.execute(sql_query_employee)
        results_employee = self.env.cr.dictfetchall()
        return results_employee

    def get_list_name_project(self,projects_table):
        list_name_project = []
        all_project = []
        for p in projects_table:
            if p['selected']:
                list_name_project.append(p['name'])
            all_project.append(p['name'])

        list_name_project = list_name_project if len(list_name_project) > 0 else all_project
        list_name_project = str(list_name_project).replace("[","(")
        list_name_project = list_name_project.replace("]",")")
        return list_name_project

    def _get_lines(self, options, line_id=None):
        lines = []
        comparison_table = options.get('date')
        context = self.env.context
        projects_table = options.get('projects')
        list_name_project = self.get_list_name_project(projects_table)
        if (context.get('print_mode') is None):
            results_project = self.get_all_project(comparison_table['date_from'],comparison_table['date_to'],list_name_project)
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
                            'columns': [{'name': self.covertFloatToTime(project["sum"])}]
                        })

            if line_id:
                results_project_in_line = self.get_project_with_id(line_id,comparison_table['date_from'],comparison_table['date_to'])
                results_employee = self.get_all_employee_of_project(line_id,comparison_table['date_from'],comparison_table['date_to'])

                lines.append({
                    'id': line_id,
                    'name': "[%s] %s" % (results_project_in_line[0]["key"], results_project_in_line[0]["name"]),
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': True,
                    'columns': [{'name': self.covertFloatToTime(results_project_in_line[0]["sum"])}]
                })
                total_employees = 0.00
                for employee in results_employee:
                    total_employees += 0.0 if employee['sum'] is None else employee['sum']
                    lines.append({
                        'id': 'task_%s' % employee["id"],
                        'name': employee["name"],
                        'level': 4,
                        'parent_id': line_id,
                        'columns': [{'name': "00:00" if employee['sum'] is None else self.covertFloatToTime(employee['sum'])}],
                        'caret_options': 'hr.employee'
                    })
                lines.append({
                    'id': 'total_%s' % line_id,
                    'class': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'level': 3,
                    'parent_id': line_id,
                    'columns': [{'name': self.covertFloatToTime(total_employees)}]
                })
            if total_all_project and not line_id:
                lines.append({
                    'id': 'total_project',
                    'class': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'level': 1,
                    'columns': [{'name': self.covertFloatToTime(total_all_project)}]
                })
        else:
            results_project = self.get_all_project(comparison_table['date_from'],comparison_table['date_to'],list_name_project)
            total_all_project = 0.00
            for project in results_project:
                if project["key"]:
                    total_all_project += project["sum"]
                    lines.append({
                        'id': str(project["id"]),
                        'name': "[%s] %s" % (project["key"], project["name"]),
                        'level': 2,
                        'unfoldable': True,
                        'unfolded': True,
                        'columns': [{'name': self.covertFloatToTime(project["sum"])}]
                    })
                    results_employee = self.get_all_employee_of_project(str(project["id"]),comparison_table['date_from'],comparison_table['date_to'])
                    total_employees = 0.00
                    for employee in results_employee:
                        total_employees += 0.0 if employee['sum'] is None else employee['sum']
                        lines.append({
                            'id': 'task_%s' % employee["id"],
                            'name': employee["name"],
                            'level': 4,
                            'parent_id': str(project["id"]),
                            'columns': [{'name': "00:00" if employee['sum'] is None else self.covertFloatToTime(
                                employee['sum'])}],
                            'caret_options': 'hr.employee'
                        })
                    lines.append({
                        'id': 'total_%s' % line_id,
                        'class': 'o_account_reports_domain_total',
                        'name': 'Total',
                        'level': 3,
                        'parent_id': str(project["id"]),
                        'columns': [{'name': self.covertFloatToTime(total_employees)}]
                    })
            if total_all_project:
                lines.append({
                    'id': 'total_project',
                    'class': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'level': 1,
                    'columns': [{'name': self.covertFloatToTime(total_all_project)}]
                })

        return lines

    def _get_templates(self):
        templates = super(TimesheetProjectEmployeeReport, self)._get_templates()
        templates['line_template'] = 'timesheet_group1.line_template_timesheet'
        templates['main_template'] = 'timesheet_group1.main_template_timesheet'
        templates['search_template'] = 'timesheet_group1.search_template_timesheet'

        return templates

    @api.multi
    def open_detail_employee(self, options, params=None):
        if not params:
            params = {}

        ctx = self.env.context.copy()
        ctx.pop('id', '')
        res_id = params.get('id').split("_")[1]
        view_id = self.env['ir.model.data'].get_object_reference("hr", "view_employee_form")[1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': "hr.employee",
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': int(res_id),
            'context': ctx,
        }

    def covertFloatToTime(self,unit_amount):
        hour_integer = int(unit_amount)
        string_hour_integer = str(hour_integer) if hour_integer >= 10 else "0" + str(hour_integer)
        minute = (unit_amount - hour_integer)*60
        minute_integer = int(minute)
        string_minute_integer = str(minute_integer) if minute_integer >= 10 else "0" + str(minute_integer)
        result = string_hour_integer + ":" + string_minute_integer
        return result

    def _build_options(self, previous_options=None):
        options = super(TimesheetProjectEmployeeReport, self)._build_options(previous_options=previous_options)
        if not previous_options or not previous_options.get("projects"):
            options["projects"] = self._get_projects()
        else:
            options["projects"] = previous_options["projects"]
        return options

    def _get_projects(self):
        projects = []
        projects_read = self.env["project.project"].search([('key','!=',None)])
        for p in projects_read:
            projects.append({
                'id': p.id,
                'name': p.name,
                'code': p.name,
                'type': p.name,
                'selected': False
            })
        return projects

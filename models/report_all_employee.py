from odoo import models, fields, api, _


class TimesheetAllEmployeeReport(models.AbstractModel):
    _name = "timesheet.all.employee.report"
    _inherit = 'account.report'
    _description = 'Timesheet All Employee  Report'
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_employees = True
    filter_all_entries = False

    def _get_report_name(self):
        return "Timesheet All Employee Task"

    def _get_columns_name(self, options):
        columns = [{'name': 'Employee'}, {'name': 'Unit amount'}]
        return columns

    def get_all_employee(self,date_from,date_to,list_employee):
        sql_query_employee_all = """
            SELECT
                   "hr_employee".name,"hr_employee".id,
                    sum("account_analytic_line".unit_amount)
            FROM hr_employee LEFT JOIN account_analytic_line
            ON "hr_employee".id = "account_analytic_line".employee_id
            WHERE "hr_employee".is_novobi IS TRUE AND "hr_employee".name IN %s
            GROUP BY "hr_employee".id
        """
        self.env.cr.execute(sql_query_employee_all % (list_employee))
        results_employee_all = self.env.cr.dictfetchall()
        for x in results_employee_all:
            if x["sum"] is None:
                x["sum"] = 0.0
        results_employee_not_worklog = list(filter(lambda x: x["sum"] == 0.0,results_employee_all))
        sql_query_employee = """
            SELECT
                   "hr_employee".name,"hr_employee".id,
                    sum("account_analytic_line".unit_amount)
            FROM hr_employee LEFT JOIN account_analytic_line
            ON "hr_employee".id = "account_analytic_line".employee_id
            WHERE "hr_employee".is_novobi IS TRUE AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s' AND "hr_employee".name IN %s
            GROUP BY "hr_employee".id
        """
        self.env.cr.execute(sql_query_employee % (date_from,date_to, list_employee))
        results_employee = self.env.cr.dictfetchall()
        return results_employee + results_employee_not_worklog

    def get_employee_with_id(self,line_id,date_from,date_to):
        sql_query_employee_in_line = """
            SELECT
               "hr_employee".name,"hr_employee".id,
                sum("account_analytic_line".unit_amount)
            FROM hr_employee LEFT JOIN account_analytic_line
            ON "hr_employee".id = %s AND "hr_employee".id = "account_analytic_line".employee_id
            WHERE "account_analytic_line".id_jira IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "hr_employee".id
        """
        sql_query_employee_in_line = sql_query_employee_in_line % (line_id,date_from,date_to)
        self.env.cr.execute(sql_query_employee_in_line)
        results_employee_in_line = self.env.cr.dictfetchall()
        return results_employee_in_line

    def get_all_project_of_employee(self,line_id,date_from,date_to):
        sql_query_project = """
            SELECT
                 "project_project".key, "project_project".name,sum("account_analytic_line".unit_amount), "project_project".id
            FROM project_project LEFT JOIN account_analytic_line
            ON "account_analytic_line".employee_id = %s AND "account_analytic_line".project_id = "project_project".id
            WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "project_project".id
        """
        sql_query_project = sql_query_project % (line_id,date_from,date_to)
        self.env.cr.execute(sql_query_project)
        result_projects = self.env.cr.dictfetchall()
        return result_projects

    def get_list_name_employee(self,empployees_table):
        list_name_employee = []
        all_employee = []
        for e in empployees_table:
            if e['selected']:
                list_name_employee.append(e['name'])
            all_employee.append(e['name'])

        list_name_employee = list_name_employee if len(list_name_employee) > 0 else all_employee
        list_name_employee = str(list_name_employee).replace("[","(")
        list_name_employee = list_name_employee.replace("]",")")
        return list_name_employee

    def _get_lines(self, options, line_id=None):
        lines = []
        comparison_table = options.get('date')
        context = self.env.context
        empployees_table = options.get('employees')
        list_name_employee = self.get_list_name_employee(empployees_table)
        if context.get('print_mode') is None:
            results_employee = self.get_all_employee(comparison_table['date_from'],comparison_table['date_to'],list_name_employee)
            total_all_project = 0.00
            if line_id is None:
                for employee in results_employee:
                    total_all_project += employee["sum"]
                    if employee["sum"] > 0.0:
                        lines.append({
                            'id': str(employee["id"]),
                            'name': employee["name"],
                            'level': 2,
                            'unfoldable': True,
                            'unfolded': False,
                            'columns': [{'name': self.covertFloatToTime(employee["sum"])}]
                        })
                    else:
                        lines.append({
                            'id': 'not_worklog',
                            'name': employee["name"],
                            'level': 2,
                            'unfoldable': False,
                            'unfolded': False,
                            'columns': [{'name': self.covertFloatToTime(employee["sum"])}]
                        })

            if line_id:
                results_employee_in_line = self.get_employee_with_id(line_id,comparison_table['date_from'],comparison_table['date_to'])
                result_projects = self.get_all_project_of_employee(line_id,comparison_table['date_from'],comparison_table['date_to'])
                lines.append({
                    'id': line_id,
                    'name': results_employee_in_line[0]["name"],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': True,
                    'columns': [{'name': self.covertFloatToTime(results_employee_in_line[0]["sum"])}]
                })
                total_projects = 0.00
                for project in result_projects:
                    total_projects += 0.0 if project['sum'] is None else project['sum']
                    lines.append({
                        'id': "project_%s" % str(project["id"]),
                        'name': project["name"],
                        'level': 4,
                        'parent_id': line_id,
                        'columns': [{'name': "00:00" if project['sum'] is None else self.covertFloatToTime(project['sum'])}],
                        'caret_options': 'project.project'
                    })
                lines.append({
                    'id': 'total_%s' % line_id,
                    'class': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'level': 3,
                    'parent_id': line_id,
                    'columns': [{'name': self.covertFloatToTime(total_projects)}]
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
            results_employee = self.get_all_employee(comparison_table['date_from'],comparison_table['date_to'],list_name_employee)
            total_all_project = 0.00
            for employee in results_employee:
                total_all_project += employee["sum"]
                lines.append({
                    'id': str(employee["id"]),
                    'name': employee["name"],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': True,
                    'columns': [{'name': self.covertFloatToTime(employee["sum"])}]
                })
                result_projects = self.get_all_project_of_employee(str(employee["id"]),comparison_table['date_from'],comparison_table['date_to'])
                total_projects = 0.00
                for project in result_projects:
                    total_projects += 0.0 if project['sum'] is None else project['sum']
                    lines.append({
                        'id': str(project["id"]),
                        'name': project["name"],
                        'level': 4,
                        'parent_id': str(employee["id"]),
                        'columns': [{'name': "00:00" if project['sum'] is None else self.covertFloatToTime(project['sum'])}],
                    })
                lines.append({
                    'id': 'total_%s' % str(employee["id"]),
                    'class': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'level': 3,
                    'parent_id': str(employee["id"]),
                    'columns': [{'name': self.covertFloatToTime(total_projects)}]
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
        templates = super(TimesheetAllEmployeeReport, self)._get_templates()
        templates['line_template'] = 'timesheet_group1.line_template_timesheet'
        templates['main_template'] = 'timesheet_group1.main_template_timesheet'
        templates['search_template'] = 'timesheet_group1.search_template_timesheet'

        return templates

    def covertFloatToTime(self,unit_amount):
        hour_integer = int(unit_amount)
        string_hour_integer = str(hour_integer) if hour_integer >= 10 else "0" + str(hour_integer)
        minute = (unit_amount - hour_integer)*60
        minute_integer = int(minute)
        string_minute_integer = str(minute_integer) if minute_integer >= 10 else "0" + str(minute_integer)
        result = string_hour_integer + ":" + string_minute_integer
        return result

    def _build_options(self, previous_options=None):
        options = super(TimesheetAllEmployeeReport, self)._build_options(previous_options=previous_options)
        if not previous_options or not previous_options.get("employees"):
            options["employees"] = self._get_employees()
        else:
            options["employees"] = previous_options["employees"]
            list_employees_is_selected = list(filter(lambda x: x["selected"] is True,options["employees"]))
            list_employees_is_unselected = []
            list_employees = self._get_employees()
            for x in list_employees_is_selected:
                list_employees_is_unselected.append(x.copy())
            list_name = []
            for x in list_employees:
                list_name.append(x["name"])
            for x in list_employees_is_unselected:
                x["selected"] = False
                if x in list_employees:
                    list_employees.remove(x)
            for x in list_employees_is_selected:
                if x["name"] in list_name:
                    list_employees.append(x)
            options["employees"] = list_employees
        return options

    def _get_employees(self):
        employees = []
        employees_read = self.env["hr.employee"].search([('is_novobi', '=',  True)])
        for e in employees_read:
            employees.append({
                'id': e.id,
                'name': e.name,
                'code': e.name,
                'type': e.name,
                'selected': False
            })
        return employees

    @api.multi
    def open_detail_project(self, options, params=None):
        if not params:
            params = {}

        ctx = self.env.context.copy()
        ctx.pop('id', '')
        res_id = params.get('id').split("_")[1]
        view_id = self.env['ir.model.data'].get_object_reference("project", "edit_project")[1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': "project.project",
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': int(res_id),
            'context': ctx,
        }
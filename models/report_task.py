from odoo import models, fields, api, _
from odoo.tools.misc import formatLang, format_date, get_user_companies

class TimesheetTaskReport(models.AbstractModel):
    _name = "timesheet.task.report"
    _inherit = 'account.report'
    _description = 'Timesheet  Report'
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_projects = True
    filter_all_entries = False

    def _get_report_name(self):
        return "Timesheet Task"

    def _get_columns_name(self, options):
        columns = [{'name': 'Project'}, {'name': 'Unit amount'}]
        return columns

    def _get_lines(self, options, line_id=None):
        lines = []
        context = self.env.context
        comparison_table = options.get('date')
        projects_table = options.get('projects')
        list_name_project = []
        all_project = []
        for p in projects_table:
            if p['selected']:
                list_name_project.append(p['name'])
            all_project.append(p['name'])

        list_name_project = list_name_project if len(list_name_project) > 0 else all_project
        list_name_project = str(list_name_project).replace("[","(")
        list_name_project = list_name_project.replace("]",")")

        sql_query_project = """
            SELECT
                   "project_project".key, "project_project".name,
                    sum("account_analytic_line".unit_amount), "project_project".id
            FROM account_analytic_line LEFT JOIN project_project
            ON "account_analytic_line".project_id = "project_project".id
            WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s' AND "project_project".name IN %s
            GROUP BY "project_project".id
        """
        sql_query_task = """
            SELECT
                 "project_task".key, "project_task".name, 
                 sum("account_analytic_line".unit_amount), "project_task".id
            FROM account_analytic_line LEFT JOIN project_task
            ON "project_task".project_id = %s AND "account_analytic_line".task_id = "project_task".id 
            WHERE to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "project_task".id
            ORDER BY "project_task".key ASC 
        """
        sql_query_project_in_line = """
            SELECT
                   "project_project".key, "project_project".name,
                    sum("account_analytic_line".unit_amount), "project_project".id
            FROM account_analytic_line LEFT JOIN project_project 
            ON "project_project".id = %s AND "account_analytic_line".project_id = "project_project".id
            WHERE "project_project".key IS NOT NULL AND to_char("account_analytic_line".date, 'YYYY-MM-DD') BETWEEN '%s' AND '%s'
            GROUP BY "project_project".id
        """
        if(context.get('print_mode') is None):
            self.env.cr.execute(sql_query_project % (comparison_table['date_from'],comparison_table['date_to'],list_name_project))
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
                            'columns': [{'name': self.covertFloatToTime(project["sum"])}]
                        })

            if line_id:
                sql_query_project_in_line = sql_query_project_in_line % (line_id,comparison_table['date_from'],comparison_table['date_to'])
                self.env.cr.execute(sql_query_project_in_line)
                results_project_in_line = self.env.cr.dictfetchall()

                sql_query_task = sql_query_task % (line_id,comparison_table['date_from'],comparison_table['date_to'])
                self.env.cr.execute(sql_query_task)
                results_task = self.env.cr.dictfetchall()

                lines.append({
                    'id': line_id,
                    'name': "[%s] %s" % (results_project_in_line[0]["key"], results_project_in_line[0]["name"]),
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': True,
                    'columns': [{'name': self.covertFloatToTime(results_project_in_line[0]["sum"])}]
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
                            'columns': [{'name': "00:00" if task['sum'] is None else self.covertFloatToTime(task['sum'])}],
                            'caret_options': 'project.task'
                        })
                lines.append({
                    'id': 'total_%s' % line_id,
                    'class': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'level': 3,
                    'parent_id': line_id,
                    'columns': [{'name': self.covertFloatToTime(total_tasks)}],
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
            self.env.cr.execute(sql_query_project % (comparison_table['date_from'],comparison_table['date_to'],list_name_project))
            results_project = self.env.cr.dictfetchall()
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
                    sql_query_task = sql_query_task % (str(project["id"]),comparison_table['date_from'], comparison_table['date_to'])
                    self.env.cr.execute(sql_query_task)
                    results_task = self.env.cr.dictfetchall()
                    total_tasks = 0.00
                    for task in results_task:
                        if task["key"]:
                            total_tasks += 0.0 if task['sum'] is None else task['sum']
                            lines.append({
                                'id': 'task_%s' % str(task["id"]),
                                'name': "[%s] %s" % (task["key"], task["name"]),
                                'level': 4,
                                'parent_id': str(project["id"]),
                                'columns': [{'name': "00:00" if task['sum'] is None else self.covertFloatToTime(task['sum'])}],
                                'caret_options': 'project.task'
                            })
                    lines.append({
                        'id': 'total_%s' % line_id,
                        'class': 'o_account_reports_domain_total',
                        'name': 'Total',
                        'level': 3,
                        'parent_id': str(project["id"]),
                        'columns': [{'name': self.covertFloatToTime(total_tasks)}],
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
        templates = super(TimesheetTaskReport, self)._get_templates()
        templates['line_template'] = 'timesheet_group1.line_template_timesheet'
        templates['main_template'] = 'timesheet_group1.main_template_timesheet'
        templates['search_template'] = 'timesheet_group1.search_template_timesheet'
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

    def covertFloatToTime(self,unit_amount):
        hour_integer = int(unit_amount)
        string_hour_integer = str(hour_integer) if hour_integer >= 10 else "0" + str(hour_integer)
        minute = (unit_amount - hour_integer)*60
        minute_integer = int(minute)
        string_minute_integer = str(minute_integer) if minute_integer >= 10 else "0" + str(minute_integer)
        result = string_hour_integer + ":" + string_minute_integer
        return result

    def _build_options(self, previous_options=None):
        options = super(TimesheetTaskReport, self)._build_options(previous_options=previous_options)
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

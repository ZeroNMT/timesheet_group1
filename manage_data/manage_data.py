from odoo.http import request
from .. import services


class ManageData():

    def create_data(self, employee_id, user):
        jira_service = services.jira_services.JiraServices(user["authorization"])

        project_list = jira_service.get_all_project()
        if project_list:
            for project in project_list:
                project_id = self.create_project(project)
                task_list = jira_service.get_all_issues_of_project(project["key"])
                if task_list:
                    for task in task_list:
                        task_id = self.create_task(project_id, task)
                        workLog_list = jira_service.get_all_worklogs_of_issue(task["key"])
                        if workLog_list:
                            self.create_workLog(employee_id, task_id, project_id, workLog_list["worklogs"])

    def create_project(self, project_info):
        project_id = request.env["project.project"].sudo().search([('key', '=',  project_info["key"])])
        if not project_id:
            project_id = request.env["project.project"].sudo().create({
                'name': project_info["name"],
                'key': project_info["key"],
                # 'user_id': ''# add project_manager_id
            })
            request.env.cr.commit()
        return project_id

    def create_task(self, project_id, task_info):
        task_id = request.env["project.task"].sudo().search([("key", '=', task_info["key"])])
        date_utils = services.date_utils.DateUtils()

        if not task_id:
            task_id = request.env["project.task"].sudo().create({
                'name': task_info["fields"]["summary"],
                'key': task_info["key"],
                'project_id':  project_id.id,
                'status': task_info["fields"]["status"]["name"],
                'last_modified': date_utils.convertString2Datetime(task_info["fields"]["updated"]),
                # 'user_id': '',
            })
            request.env.cr.commit()
        return task_id

    def search_employee(self, name):
        employee = request.env["hr.employee"].sudo().search([('name', '=', name)])
        if not employee:
            return employee.id
        else:
            return None

    def create_workLog(self, employee_id, task_id, project_id, workLog_list):
        lst = []
        date_utils = services.date_utils.DateUtils()
        for workLog in workLog_list:
            datetime = date_utils.convertString2Datetime(workLog["started"])
            name_employee = workLog["author"]["key"]
            lst.append({
                'name': workLog["comment"],
                'task_id': task_id.id,
                'project_id': project_id.id,
                'employee_id': employee_id.id if name_employee == employee_id.name else self.search_employee(name_employee),
                'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                'id_jira': workLog["id"]
            })
        for item in lst:
            request.env["account.analytic.line"].sudo().create(item)
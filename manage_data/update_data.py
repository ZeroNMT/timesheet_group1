from odoo.http import request
from odoo import exceptions,_
from .. import services


class UpdateData():

    def update_data(self):
        if not request.env.user["authorization"]:
            raise exceptions.UserError(_("You isn't Jira's account"))
        else:
            jira_service = services.jira_services.JiraServices(request.env.user["authorization"])

            project_list = jira_service.get_all_project()
            if project_list:
                for project in project_list:
                    lead_project = jira_service.get_project(project["key"])
                    if lead_project:
                        project_id = self.update_project(project, lead_project["lead"])
                        task_list = jira_service.get_all_issues_of_project(project["key"])
                        if task_list:
                            for task in task_list:
                                task_id = self.update_task(project_id, task)
                                workLog_list = jira_service.get_all_worklogs_of_issue(task["key"])
                                if workLog_list:
                                    self.update_worklog(task_id, project_id, workLog_list["worklogs"])

    def create_user(self, username):
        userDB = request.env["res.users"].sudo().search([('name', '=', username)])
        if not userDB:
            userDB = request.env["res.users"].sudo().create({
                'name': username,
                'login': username,
                'active': True,
                'employee': True,
                'employee_ids': [(0, 0, {'name': username})]
            })
        return userDB

    def update_project(self, project_info, lead_project):
        project_id = request.env["project.project"].sudo().search([('key', '=',  project_info["key"])])
        if not project_id:

            project_id = request.env["project.project"].sudo().create({
                'name': project_info["name"],
                'key': project_info["key"],
                'user_id': self.create_user(lead_project["name"]).id
            })
        return project_id

    def update_task(self, project_id, task_info):
        task_id = request.env["project.task"].sudo().search([("key", '=', task_info["key"])])
        date_utils = services.date_utils.DateUtils()

        if not task_id:
            task_id = request.env["project.task"].sudo().create({
                'name': task_info["fields"]["summary"],
                'key': task_info["key"],
                'project_id':  project_id.id,
                'status': task_info["fields"]["status"]["name"],
                'last_modified': date_utils.convertString2Datetime(task_info["fields"]["updated"]),
                'user_id': self.create_user(task_info["fields"]["assignee"]["name"]).id
            })
        return task_id

    def search_employee(self, name):
        employee = request.env["hr.employee"].sudo().search([('name', '=', name)])
        if not employee:
            self.create_user(name)
            return request.env["hr.employee"].sudo().search([('name', '=', name)])
        else:
            return employee

    def update_worklog(self, task_id, project_id, workLog_list):
        worklogDB = request.env["account.analytic.line"].sudo().search([('task_id', '=', task_id.id),
                                                                        ('unit_amount', '!=', 0.0)])
        dic = {}
        for worklog in worklogDB:
            dic.update({int(worklog.id_jira): worklog.id})

        create_lst = []
        date_utils = services.date_utils.DateUtils()
        for workLog in workLog_list:
            if int(workLog["id"]) not in dic:
                create_lst.append({
                    'name': workLog["comment"],
                    'task_id': task_id.id,
                    'project_id': project_id.id,
                    'employee_id': self.search_employee(workLog["author"]["key"]).id,
                    'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                    'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                    'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                    'id_jira': workLog["id"],
                    "not_update": "Jira"

                })
            else:
                record = request.env["account.analytic.line"].sudo().browse(dic[int(workLog["id"])])
                update_worklog = date_utils.convertString2Datetime(workLog["updated"])
                datetime = date_utils.convertString2Datetime(workLog["started"])
                if update_worklog != record.last_modified:
                    record.sudo().write({
                        'name': workLog["comment"],
                        'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                        'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                        'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                        "not_update": "Jira"
                    })
                    request.env.cr.commit()
                del dic[int(workLog["id"])]

        for key, value in dic.items():
            request.env["account.analytic.line"].sudo().browse(value).unlink()

        for item in create_lst:
            request.env["account.analytic.line"].sudo().create(item)
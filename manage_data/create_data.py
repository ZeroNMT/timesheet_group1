from odoo.http import request
from .. import services


class CreateData():

    def create_data(self, employee_id, username):
        jira_service = services.jira_services.JiraServices(request.session["authorization"])

        project_list = jira_service.get_all_project()
        if project_list:
            for project in project_list:
                lead_project = jira_service.get_project(project["key"])
                if lead_project:
                    project_id = self.create_project(username, project, lead_project["lead"])
                    task_list = jira_service.get_all_issues_of_project(project["key"])
                    if task_list:
                        for task in task_list:
                            task_id = self.create_task(project_id, task)
                            workLog_list = jira_service.get_all_worklogs_of_issue(task["key"])
                            if workLog_list:
                                self.create_workLog(employee_id, task_id, project_id, workLog_list["worklogs"])

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

    def create_project(self, username, project_info, lead_project):
        project_id = request.env["project.project"].sudo().search([('key', '=',  project_info["key"])])
        user = request.env["res.users"].sudo().search([('name', '=', username)])
        if not project_id:
            project_id = request.env["project.project"].sudo().create({
                'name': project_info["name"],
                'key': project_info["key"],
                'user_id': self.create_user(lead_project["name"]).id,
                'user_ids': [(4, user.id, 0)]
            })
        else:
            project_id.sudo().write({'user_ids': [(4, user.id, 0)]})
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
                'user_id': self.create_user(task_info["fields"]["assignee"]["name"]).id if task_info["fields"]["assignee"]
                                                                                                        else ''
            })
        return task_id

    def search_employee(self, name):
        employee = request.env["hr.employee"].sudo().search([('name', '=', name)])
        if not employee:
            self.create_user(name)
            return request.env["hr.employee"].sudo().search([('name', '=', name)])
        else:
            return employee

    def create_workLog(self, employee_id, task_id, project_id, workLog_list):
        worklogDB = request.env["account.analytic.line"].sudo().search([('task_id', '=', task_id.id)])
        dic = {}
        for worklog in worklogDB:
            dic.update({int(worklog.id_jira): True})

        lst = []
        date_utils = services.date_utils.DateUtils()
        for workLog in workLog_list:
            if int(workLog["id"]) not in dic:
                datetime = date_utils.convertString2Datetime(workLog["started"])
                name = workLog["author"]["key"]
                lst.append({
                    'name': workLog["comment"],
                    'task_id': task_id.id,
                    'project_id': project_id.id,
                    'employee_id': employee_id.id if name == employee_id.name else self.search_employee(name).id,
                    'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                    'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                    'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                    'id_jira': workLog["id"],
                    'not_update_jira': 'True'
                })
        for item in lst:
            request.env["account.analytic.line"].sudo().create(item)
        # if len(lst)>1:
        #     lst_t1 = lst[0:int(len(lst)/2)]
        #     lst_t2 = lst[int(len(lst)/2):len(lst)]
        #     request.env["account.analytic.line"].sudo().with_delay().create_workLog(lst_t1)
        #     request.env["account.analytic.line"].sudo().with_delay().create_workLog(lst_t2)
        # elif len(lst)==1:
        #     request.env["account.analytic.line"].sudo().with_delay().create_workLog(lst)
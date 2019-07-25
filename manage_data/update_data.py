from odoo.http import request
from odoo import exceptions,_
from .. import services


class UpdateData():

    def update_data(self, username):

        userDB = request.env["res.users"].search([('login', '=', username)])
        if not userDB.authorization:
            raise exceptions.UserError(_("You isn't Jira's account"))
        else:
            authorization = services.aes_cipher.AESCipher().decrypt(userDB.authorization)
            jira_service = services.jira_services.JiraServices(authorization)
            project_list = jira_service.get_all_project()
            if project_list:
                for project in project_list:
                    lead_project = jira_service.get_project(project["key"])
                    if lead_project:
                        project_id = self.update_project(username, project, lead_project["lead"])
                        task_list = jira_service.get_all_issues_of_project(project["key"])
                        if task_list:
                            for task in task_list:
                                task_id = self.update_task(project_id, task)
                                workLog_list = jira_service.get_all_worklogs_of_issue(task["key"])
                                if workLog_list:
                                    self.update_worklog(task_id, project_id, workLog_list["worklogs"])

    def create_user(self, username, email):
        userDB = request.env["res.users"].sudo().search([('login', '=', email)])
        if not userDB.login:
            userDB = request.env["res.users"].sudo().create({
                'name': username,
                'login': email,
                'email': email,
                'active': True,
                'employee': True,
                'employee_ids': [(0, 0, {'name': username,
                                         'work_email': email,
                                         'is_novobi': True})]
            })
        return userDB

    def update_project(self, username, project_info, lead_project):
        project_id = request.env["project.project"].sudo().search([('key', '=',  project_info["key"])])
        user = request.env["res.users"].sudo().search([('login', '=', username)])
        if not project_id:
            project_id = request.env["project.project"].sudo().create({
                'name': project_info["name"],
                'key': project_info["key"],
                'user_id': self.create_user(lead_project["displayName"], lead_project["key"]).id,
                'user_ids': [(4, user.id, 0)]
            })
        else:
            project_id.sudo().write({'user_ids': [(4, user.id, 0)]})
            request.env.cr.commit()
        return project_id

    def update_task(self, project_id, task_info):
        task_id = request.env["project.task"].sudo().search([("key", '=', task_info["key"])])
        date_utils = services.date_utils.DateUtils()

        if not task_id:
            assignee = task_info["fields"]["assignee"]
            task_id = request.env["project.task"].sudo().create({
                'name': task_info["fields"]["summary"],
                'key': task_info["key"],
                'project_id':  project_id.id,
                'status': task_info["fields"]["status"]["name"],
                'last_modified': date_utils.convertString2Datetime(task_info["fields"]["updated"]),
                'user_id': self.create_user(assignee["displayName"], assignee["key"]).id if task_info["fields"]["assignee"]
                                                                                                        else ''
            })
        return task_id

    def search_employee(self, name, login):
        employee = request.env["hr.employee"].sudo().search([('work_email', '=', login)])
        if not employee:
            self.create_user(name, login)
            return request.env["hr.employee"].sudo().search([('work_email', '=', login)])
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
            datetime = date_utils.convertString2Datetime(workLog["started"])
            if int(workLog["id"]) not in dic:
                create_lst.append({
                    'name': workLog["comment"],
                    'task_id': task_id.id,
                    'project_id': project_id.id,
                    'employee_id': self.search_employee(workLog["author"]["displayName"], workLog["author"]["key"]).id,
                    'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                    'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                    'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                    'id_jira': workLog["id"]
                })
            else:
                record = request.env["account.analytic.line"].sudo().browse(dic[int(workLog["id"])])
                update_worklog = date_utils.convertString2Datetime(workLog["updated"])
                if update_worklog != record.last_modified:
                    record.sudo().with_context(not_update_jira=True).write({
                        'name': workLog["comment"],
                        'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                        'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                        'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                    })
                    request.env.cr.commit()
                del dic[int(workLog["id"])]

        for key, value in dic.items():
            request.env["account.analytic.line"].sudo().browse(value).unlink()

        for item in create_lst:
            request.env["account.analytic.line"].sudo().with_context(not_update_jira=True).create(item)


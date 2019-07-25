from odoo.http import request
from odoo import exceptions,_
from .. import services


class UpdateData():
    projects_list = {}
    employees_list = {}
    users_list = {}
    ticket_list = {}
    data_list = {}

    def __init__(self, username):
        userDB = request.env["res.users"].search([('login', '=', username)])
        if not userDB.authorization:
            raise exceptions.UserError(_("You isn't Jira's account"))
        else:
            authorization = services.aes_cipher.AESCipher().decrypt(userDB.authorization)
            self.username = username
            self.jira_api = services.jira_services.JiraServices(authorization)

    def search_projects(self):
        projectsDB = request.env["project.project"].search(['key', '!=', None])
        for project in projectsDB:
            self.projects_list.update({
                project.key: project
            })

    def create_project(self, key_project):
        projectDB = self.projects_list.get(key_project)
        project_info = self.jira_api.get_project(key_project)
        project_manager = self.create_user({
            'displayName': project_info["lead"]["displayName"],
            'email': project_info["lead"]["key"]
        })
        user = self.users_list.get(self.username)

        if projectDB is None:
            projectDB = request.env["project.project"].sudo().create({
                'name': project_info["name"],
                'key': key_project,
                'user_id': project_manager.id,
                'user_ids': [(4, user.id, 0)]
            })
            self.projects_list.update({key_project: projectDB})
        else:
            projectDB.sudo().write({'user_ids': [(4, user.id, 0)]})
            request.env.cr.commit()
        return projectDB

    def search_employees(self):
        employeesDB = request.env["hr.employee"].search(['is_novobi', '!=', None])
        for employee in employeesDB:
            self.employees_list.update({
                employee.work_email: employee
            })

    def search_users(self):
        usersDB = request.env["res.users"].search(['authorization', '!=', None])
        for user in usersDB:
            self.users_list.update({
                user.login: user
            })

    def create_user(self, agrs):
        userDB = self.users_list.get(agrs["email"])
        if userDB is None:
            userDB = request.env["res.users"].sudo().create({
                'name': agrs["displayName"],
                'login': agrs["email"],
                'email': agrs["email"],
                'active': True,
                'employee': True,
                'employee_ids': [(0, 0, {'name': agrs["displayName"],
                                         'work_email': agrs["email"],
                                         'is_novobi': True})]
            })
            self.users_list.update({agrs["email"]: userDB})
        return userDB

    def search_tickets(self):
        ticketsDB = request.env["project.task"].search(['key', '!=', None])
        for ticket in ticketsDB:
            self.ticket_list.update({
                ticket.key: ticket
            })

    def update_data(self):
        self.search_users()
        self.search_projects()
        self.search_tickets()
        all_tickets = self.jira_api.get_all_tickets()
        date_utils = services.date_utils.DateUtils()
        for t in all_tickets:
            projectDB = self.create_project(t["fields"]["project"]["key"])
            assignee = t["fields"]["assignee"]
            worklogs_jira = self.jira_api.get_all_worklogs_of_issue(t["key"])["worklogs"]
            workLogs = []
            for workLog in worklogs_jira:
                datetime = date_utils.convertString2Datetime(workLog["started"])
                self.create_user({
                    'displayName': workLog["author"]["displayName"],
                    'email': workLog["author"]["key"]
                })
                workLogs.append({
                    'name': workLog["comment"],
                    'project_id': projectDB.id,
                    'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                    'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                    'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                    'id_jira': workLog["id"]
                })

            self.data_list.append({
                'name': t["fields"]["summary"],
                'key': t["key"],
                'project_id': projectDB.id,
                'status': t["fields"]["status"]["name"],
                'last_modified': date_utils.convertString2Datetime(t["fields"]["updated"]),
                'user_id': self.create_user({
                    'displayName': assignee["displayName"],
                    'email': assignee["key"]
                }) if assignee else '',
                'workLogs': workLogs
            })




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


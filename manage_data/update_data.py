from odoo.http import request
from odoo import exceptions,_
from .. import services


class UpdateData():
    projects_list = {}
    employees_list = {}
    users_list = {}
    ticket_list = {}
    worklog_list = {}
    data_list = []

    def __init__(self, username):
        userDB = request.env["res.users"].search([('login', '=', username)])
        if not userDB.authorization:
            raise exceptions.UserError(_("You isn't Jira's account"))
        else:
            authorization = services.aes_cipher.AESCipher().decrypt(userDB.authorization)
            self.username = username
            self.jira_api = services.jira_services.JiraServices(authorization)

    def search_projects(self):
        projectsDB = request.env["project.project"].sudo().search([('key', '!=', None)])
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
            request.env["project.project"].sudo().browse(projectDB.id).write({'user_ids': [(4, user.id, 0)]})
            request.env.cr.commit()
        return projectDB

    def search_employees(self):
        employeesDB = request.env["hr.employee"].sudo().search([('is_novobi', '!=', None)])
        for employee in employeesDB:
            self.employees_list.update({
                employee.work_email: employee
            })

    def search_users(self):
        usersDB = request.env["res.users"].sudo().search([('is_novobi', '!=', None)])
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
                                         'is_novobi': True})],
                'is_novobi': True
            })
            self.users_list.update({agrs["email"]: userDB})
        return userDB

    def search_tickets(self):
        ticketsDB = request.env["project.task"].sudo().search([('key', '!=', None)])
        for ticket in ticketsDB:
            self.ticket_list.update({
                ticket.key: ticket
            })

    def update_ticket(self, agrs, ticketDB):
        request.env["project.task"].sudo().browse(ticketDB.id).write({
            'last_modified': agrs["last_modified"],
            'user_id': agrs["user_id"]
        })
        request.env.cr.commit()

    def create_ticket(self, agrs):
        val = agrs.copy()
        del val["workLogs"]
        return request.env["project.task"].sudo().create(val)

    def search_worklogs(self):
        worklogDB = request.env["account.analytic.line"].sudo().search([('id_jira', '!=', None)])
        for workLog in worklogDB:
            self.worklog_list.update({
                workLog.id_jira: workLog
            })

    def update_worklog(self, agrs, worklogDB):
        request.env["account.analytic.line"].sudo().browse(worklogDB.id).with_context(not_update_jira=True).write({
            'name': agrs["name"],
            'unit_amount': agrs["unit_amount"] / (60 * 60),
            'last_modified': agrs["last_modified"],
            'date': agrs["date"],
        })
        request.env.cr.commit()

    def create_worklog(self, task_id, agrs):
        request.env["account.analytic.line"].sudo().with_context(not_update_jira=True).create({
            'name': agrs["name"],
            'task_id': task_id,
            'employee_id': self.employees_list[agrs["key_employee"]].id,
            'project_id': agrs["project_id"],
            'unit_amount': agrs["unit_amount"],
            'date': agrs["date"],
            'last_modified': agrs["last_modified"],
            'id_jira': agrs["id_jira"]

        })

    def transform_data(self):
        self.search_users()
        self.search_projects()
        self.search_tickets()
        self.search_worklogs()

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
                    'key_employee': workLog["author"]["key"],
                    'project_id': projectDB.id,
                    'unit_amount': workLog["timeSpentSeconds"] / (60 * 60),
                    'date': date_utils.convertToLocalTZ(datetime, workLog["updateAuthor"]["timeZone"]),
                    'last_modified': date_utils.convertString2Datetime(workLog["updated"]),
                    'id_jira': workLog["id"]
                })
                if self.worklog_list.get(workLog["id"]):
                    del self.worklog_list[workLog["id"]]

            self.data_list.append({
                'name': t["fields"]["summary"],
                'key': t["key"],
                'project_id': projectDB.id,
                'status': t["fields"]["status"]["name"],
                'last_modified': date_utils.convertString2Datetime(t["fields"]["updated"]),
                'user_id': self.create_user({
                    'displayName': assignee["displayName"],
                    'email': assignee["key"]
                }).id if assignee else '',
                'workLogs': workLogs
            })
            if self.ticket_list.get(t["key"]):
                del self.ticket_list[t["key"]]

        for key, value in self.worklog_list.items():
            request.env["account.analytic.line"].sudo().browse(value.id).unlink()
        for key, value in self.ticket_list.items():
            request.env["project.task"].sudo().browse(value.id).sudo().unlink()

        len_data = len(self.data_list)
        if len_data != 0:
            half_len_data = len_data//2
            request.env['account.analytic.line'].sudo().with_delay().update_data(self.username, self.data_list[:half_len_data])
            request.env['account.analytic.line'].sudo().update_data(self.username, self.data_list[half_len_data:])

    def update_data(self, data_list):
        self.search_employees()
        self.search_worklogs()
        self.search_tickets()
        for ticket in data_list:
            ticketDB = self.ticket_list.get(ticket["key"])
            if ticketDB and ticketDB["last_modified"] != ticket["last_modified"]:
                for worklog in ticket["workLogs"]:
                    worklogDB = self.worklog_list.get(worklog["id_jira"])
                    if worklogDB:
                        self.update_worklog(worklog, worklogDB)
                    else:
                        self.create_worklog(ticketDB.id, worklog)
                self.update_ticket(ticket, ticketDB)
            elif ticketDB is None:
                ticketDB = self.create_ticket(ticket)
                for worklog in ticket["workLogs"]:
                    self.create_worklog(ticketDB.id, worklog)

from odoo.http import request
from odoo import exceptions,_
from .. import services
import datetime


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

    def create_ticket(self, agrs):
        return request.env["project.task"].sudo().create(agrs)

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

    def create_worklog(self, agrs):
        request.env["account.analytic.line"].sudo().with_context(not_update_jira=True).create({
            'name': agrs["name"],
            'task_id': agrs["task_id"],
            'employee_id': agrs["employee_id"],
            'project_id': agrs["project_id"],
            'unit_amount': agrs["unit_amount"],
            'date': agrs["date"],
            'last_modified': agrs["last_modified"],
            'id_jira': agrs["id_jira"] if agrs.get("id_jira") else None
        })

    def transform_data(self):
        all_projects = self.jira_api.get_all_project()
        for project in all_projects:
            request.env['account.analytic.line'].sudo().with_delay().update_data(self.username, project["key"])

    def update_data(self, key_project):
        self.search_users()
        self.search_tickets()

        date_utils = services.date_utils.DateUtils()
        projectDB = self.create_project(key_project)
        tickets = self.jira_api.get_all_issues_of_project(key_project)
        for t in tickets:
            assignee = t["fields"]["assignee"]
            if self.ticket_list.get(t["key"]) is None:
                ticketDB = self.create_ticket({
                    'name': t["fields"]["summary"],
                    'key': t["key"],
                    'project_id': projectDB.id,
                    'status': t["fields"]["status"]["name"],
                    'last_modified': date_utils.convertString2Datetime(t["fields"]["updated"]),
                    'user_id': self.create_user({
                        'displayName': assignee["displayName"],
                        'email': assignee["key"]
                    }).id if assignee else '',
                })
                self.create_worklog({
                        'name': '',
                        'task_id': ticketDB.id,
                        'employee_id': '',
                        'project_id': projectDB.id,
                        'unit_amount': 0.0,
                        'date': datetime.datetime.now(),
                        'last_modified': datetime.datetime.now(),
                })

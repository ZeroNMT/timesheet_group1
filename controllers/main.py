# -*- coding: utf-8 -*-

from odoo import http
import base64
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from .. import web_services

class HomeExtend(Home):
    @http.route('/web/login',type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':

            login = base64.b64encode((request.params['login'] + ':' + request.params['password']).encode('ascii'))
            jira_services =  web_services.jira_services.JiraServices(login)

            loginResult = jira_services.login_jira(request.params['login'],request.params["password"])
            if loginResult is not None:
                UserDB = request.env['res.users'].sudo().with_context(active_test=False)

                currentUser = UserDB.search([('login', '=', request.params['login'])])


                if not currentUser:
                    user = {
                        'name' : request.params['login'],
                        'login' : request.params['login'],
                        'password': request.params['password'],
                        'authorization' : login,
                        'active': True
                    }
                    currentUser = request.env.ref('base.default_user').sudo().copy(user)

                    getIssues_Result = jira_services.getAllIssues(request.params["login"])
                    if getIssues_Result is not None:
                        if len(getIssues_Result) !=0:
                            employee = request.env['hr.employee'].sudo().create({
                                'name' : getIssues_Result[0]["fields"]["assignee"]["displayName"]
                            })
                        taskDB = request.env['project.task'].sudo()
                        projectDB = request.env['project.project'].sudo()
                        timesheetDB = request.env['account.analytic.line'].sudo()

                        for issue in getIssues_Result:
                            task = taskDB.create({
                                'name': issue["key"]
                            })
                            project = projectDB.create({
                                'name': issue["fields"]["project"]["name"]
                            })
                            timesheetDB.create({
                                'task_id': task.id,
                                'project_id': project.id,
                                'employee_id': employee.id
                            })

                currentUser.sudo().write({'password' : request.params['password']})

                request.env.cr.commit()

        return super().web_login(redirect, **kw)



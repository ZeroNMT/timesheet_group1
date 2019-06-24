from odoo import http
import base64
import requests as callAPI
from odoo.http import request
from odoo.addons.web.controllers.main import Home
class HomeExtend(Home):
    @http.route('/web/login',type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':

            api_url = 'https://jira.novobi.com'

            httpResponse = callAPI.post(
                url = api_url + "/rest/auth/1/session",
                json = {
                    'username': request.params['login'],
                    'password': request.params['password'],
                }
            )

            jira_data = httpResponse.json()

            if httpResponse.status_code == 200:
                UserDB = request.env['res.users'].sudo().with_context(active_test=False)

                currentUser = UserDB.search([('login', '=', request.params['login'])])


                if not currentUser:
                    token = base64.b64encode((request.params['login'] + ':' + request.params['password']).encode('ascii'))
                    user = {
                        'name' : request.params['login'],
                        'login' : request.params['login'],
                        'password': request.params['password'],
                        'authorization' : token,
                        'active': True
                    }
                    currentUser = request.env.ref('base.default_user').sudo().copy(user)

                    reponse = callAPI.post(
                        url = api_url + "/rest/api/2/search",
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': 'Basic' + ' ' + str(token.decode("utf-8"))
                        },
                        json={
                            "jql": "assignee = %s" % (request.params['login'].replace("@", "\\u0040")),
                            "startAt": 0,
                            "maxResults": 50,
                            "fields": [
                                "project",
                                "assignee",
                                "status"
                            ]
                        }
                    )
                    issues = reponse.json()["issues"]
                    if len(issues) !=0:
                        employee = request.env['hr.employee'].sudo().create({
                            'name' : issues[0]["fields"]["assignee"]["displayName"]
                        })
                    taskDB = request.env['project.task'].sudo()
                    projectDB = request.env['project.project'].sudo()
                    timesheetDB = request.env['account.analytic.line'].sudo()

                    for issue in issues:
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



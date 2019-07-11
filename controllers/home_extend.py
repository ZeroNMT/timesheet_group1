# -*- coding: utf-8 -*-

from odoo import http
import base64
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from .. import services
from ..manage_data import create_data

class HomeExtend(Home):
    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':
            token = base64.b64encode((request.params['login'] + ':' + request.params['password']).encode('ascii'))

            jira_services = services.jira_services.JiraServices(token)
            loginResult = jira_services.login_jira(request.params['login'], request.params["password"])

            if loginResult:
                UserDB = request.env['res.users'].sudo().with_context(active_test=False)
                currentUser = UserDB.search([('login', '=', request.params['login'])])
                if not currentUser:
                    user = {
                        'name': request.params['login'],
                        'login': request.params['login'],
                        'password': request.params['password'],
                        'authorization': token,
                        'active': True,
                        'employee_ids': [(0, 0, {'name': request.params['login']})]
                    }
                    currentUser = request.env.ref('base.default_user').sudo().copy(user)
                elif not currentUser.authorization:
                    currentUser.sudo().write({'authorization': token})

                create_data.CreateData().create_data(currentUser.employee_ids[0], token, request.params['login'])
                currentUser.sudo().write({'password': request.params['password']})
                request.env.cr.commit()

        return super().web_login(redirect, **kw)





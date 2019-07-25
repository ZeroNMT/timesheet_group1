# -*- coding: utf-8 -*-

from odoo import http
import base64
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from .. import services
from .. import manage_data

class HomeExtend(Home):
    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':
            token = base64.b64encode((request.params['login'] + ':' + request.params['password']).encode('ascii')).decode("utf-8")

            jira_services = services.jira_services.JiraServices(token)
            loginResult = jira_services.login_jira(request.params['login'], request.params["password"])
            if loginResult:
                token = services.aes_cipher.AESCipher().encrypt(token)

                UserDB = request.env['res.users'].sudo().with_context(active_test=False)
                currentUser = UserDB.search([('login', '=', request.params['login'])])
                user_jira = jira_services.get_user(request.params['login'])
                if not currentUser:
                    user = {
                        'name': user_jira["displayName"],
                        'login': request.params['login'],
                        'email': request.params['login'],
                        'password': request.params['password'],
                        'authorization': token,
                        'active': True,
                        'employee_ids': [(0, 0, {'name': user_jira["displayName"],
                                                 'work_email': request.params['login'],
                                                 'is_novobi': True})],
                        'tz': user_jira["timeZone"]
                    }
                    currentUser = request.env.ref('base.default_user').sudo().copy(user)
                elif not currentUser.authorization:
                    currentUser.sudo().write({
                        'authorization': token,
                        'tz': user_jira["timeZone"]
                    })

                request.env['account.analytic.line'].sudo().with_delay().update_data(request.params['login'])
                currentUser.sudo().write({
                    'password': request.params['password'],
                    'authorization': token
                })
                request.env.cr.commit()

        return super().web_login(redirect, **kw)





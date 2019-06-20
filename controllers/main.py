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
                    user = {
                        'name' : request.params['login'],
                        'login' : request.params['login'],
                        'password': request.params['password'],
                        'authorization' : base64.b64encode((request.params['login'] + ':' + request.params['password']).encode('ascii')),
                        'active': True
                    }
                    currentUser = request.env.ref('base.default_user').sudo().copy(user)


                currentUser.sudo().write({'password' : request.params['password']})

                request.env.cr.commit()

        return super().web_login(redirect, **kw)



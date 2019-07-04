from odoo.http import request
from .. import services

class ManageData():

    def create_data(self, user):
        jira_service = services.jira_services.JiraServices(user["authorization"])

        project_list = jira_service.get_all_project()
        if project_list:
            pass
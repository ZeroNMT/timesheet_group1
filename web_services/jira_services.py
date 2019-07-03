# -*- coding: utf-8 -*-

import requests
from odoo.tools import date_utils
from odoo import fields
import time
class JiraServices():

    def __init__(self, login):
        self.api_url = 'https://jira.novobi.com'
        self.header = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + ' ' + str(login.decode("utf-8"))
        }

    def login_jira(self, username, password):
        reponse = requests.post(
            url = self.api_url + "/rest/auth/1/session",
            json = {
                'username': username,
                'password': password,
            }
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            return None

    def getAllIssues(self, username):
        startAt = 0
        maxResults = 50
        allIssues = []
        while (True):
            reponse = requests.post(
                url = self.api_url + "/rest/api/2/search",
                headers = self.header,
                json={
                    "jql": "assignee = %s" % (username.replace("@", "\\u0040")),
                    "startAt": startAt,
                    "maxResults": maxResults,
                    "fields": [
                        "project",
                        "assignee",
                        "status",
                        "worklog",
                        "summary"
                    ]
                }
            )
            if reponse.status_code == 200:
                allIssues.extend(reponse.json()["issues"])
                if len(reponse.json()["issues"]) == (maxResults - startAt):
                    startAt = maxResults
                    maxResults += 50
                else:
                    break

        if reponse.status_code == 200:
            return allIssues
        else:
            return None

    def get_user(self, username):
        reponse = requests.get(
            url = self.api_url + "/rest/api/2/user",
            headers = self.header,
            params = {
                "username": username
            }
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            return None

    def add_worklog(self, agr):
        reponse = requests.post(
            url=self.api_url + "/rest/api/2/issue/%s/worklog" %(agr["task_key"]),
            headers=self.header,
            json={
                "comment": agr["description"],
                "started": agr["date"],
                "timeSpentSeconds": int(agr["unit_amount"]*60*60)
            }
        )
        if reponse.status_code == 201:
            print("Success !!!")
            return reponse.json()
        else:
            print(agr)
            print(reponse)
            return None

    def update_worklog(self, agr):
        reponse = requests.put(
            url=self.api_url + "/rest/api/2/issue/%s/worklog/%s" %(agr["task_key"], agr["worklog_id"]),
            headers=self.header,
            data={
                "comment": agr["description"],
                "started": agr["date"],
                "timeSpentSeconds": int(agr["unit_amount"]*60*60)
            }
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            return None

    def convertString2Date(self, strFull):
        strDateTime = strFull[:strFull.find(".")].replace("T", " ")
        dateTime = fields.Datetime.to_datetime(strDateTime)
        strTZ = strFull[-4:]
        if strFull.find("+") == -1:
            strDateTime = date_utils.add(dateTime, hours=int(strTZ[:2]), minutes=int(strTZ[2:]))
        else:
            strDateTime = date_utils.subtract(dateTime, hours=int(strTZ[:2]), minutes=int(strTZ[2:]))
        return strDateTime

    def convertDatetime2String(self, datetime):
        strDatetime = fields.Datetime.to_string(datetime).replace(" ", "T") + ".000" + "+0000"
        return strDatetime
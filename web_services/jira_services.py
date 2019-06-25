# -*- coding: utf-8 -*-

import requests

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
                        "worklog"
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
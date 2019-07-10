# -*- coding: utf-8 -*-

import requests


class JiraServices():

    def __init__(self, login):
        self.api_url = "https://jira.novobi.com"
        self.header = {
            "Content-Type": "application/json",
            "Authorization": "Basic" + " " + str(login.decode("utf-8"))
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

    def get_user(self, username):
        reponse = requests.get(
            url=self.api_url + "/rest/api/2/user",
            headers=self.header,
            params={
                "username": username
            }
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            return None

    def get_all_project(self):
        reponse = requests.get(
            url=self.api_url + "/rest/api/2/project",
            headers=self.header,
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            return None

    def get_project(self, key_project):
        reponse = requests.get(
            url=self.api_url + "/rest/api/2/project/%s" % key_project,
            headers=self.header,
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            return None

    def get_all_issues_of_project(self, key_project):
        startAt = 0
        maxResults = 1000
        allIssues = []
        while (True):
            reponse = requests.post(
                url=self.api_url + "/rest/api/2/search",
                headers=self.header,
                json={
                    "jql": "project = %s" % key_project,
                    "startAt": startAt,
                    "maxResults": maxResults,
                    "fields": [
                        "assignee",
                        "status",
                        "summary",
                        "project",
                        "updated",
                        "worklog"
                    ]
                }
            )
            if reponse.status_code == 200:
                allIssues.extend(reponse.json()["issues"])
                if len(reponse.json()["issues"]) == (maxResults - startAt):
                    startAt = maxResults
                    maxResults += 1000
                else:
                    break
            else:
                break

        if reponse.status_code == 200:
            return allIssues
        else:
            return None

    def get_all_worklogs_of_issue(self, key_task):
        reponse = requests.get(
            url=self.api_url + "/rest/api/2/issue/%s/worklog" % key_task,
            headers=self.header
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
            print(reponse)
            return None

    def update_worklog(self, agr):
        data = {}
        if agr.get("name"):
            data.update({"comment": agr["name"]})
        if agr.get("date"):
            data.update({"started": agr["date"]})
        if agr.get("unit_amount"):
            data.update({"timeSpentSeconds": int(agr["unit_amount"]*60*60)})

        reponse = requests.put(
            url=self.api_url + "/rest/api/2/issue/TIME-4/worklog/47223",
            headers=self.header,
            data=data
        )
        if reponse.status_code == 200:
            return reponse.json()
        else:
            print(reponse, reponse.json(), sep="\n")
            return None

{
    'name': 'Timesheet in Odoo of Jira',
    'depends': [
        'base',
        'analytic',
        'project'
    ],
    'author': 'Group1',
    'data': [
        'security/ir.model.access.csv',
        'security/timesheet_security.xml',
        'views/timesheet_menu.xml',
        'views/timesheet_views.xml',
    ],
    'application': True,

}
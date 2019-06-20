{
    'name': 'Timesheet in Odoo of Jira',
    'depends': [
        'base',
        'analytic',
    ],
    'author': 'Group1',
    'data': [
        'security/timesheet_security.xml',
        'security/ir.model.access.csv',
        'views/timesheet_menu.xml',
        'views/timesheet_views.xml',
    ],
    'application': True,

}
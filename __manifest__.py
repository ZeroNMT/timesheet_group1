{
    'name': 'Timesheet in Odoo of Jira',
    'depends': [
        'hr_timesheet',
    ],
    'author': 'Group1',
    'data': [
        'security/timesheet_security.xml',
        'security/ir.model.access.csv',
        'views/timesheet_menu.xml',
    ],
    'application': True,

}
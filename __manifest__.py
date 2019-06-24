{
    'name': 'Timesheet Jira',
    'depends': [
        'base',
        'analytic',
        'project',
        'hr',
        'uom'
    ],
    'author': 'Group1',
    'data': [
        'security/ir.model.access.csv',
        'views/timesheet_menu.xml',
        'views/timesheet_views.xml',
    ],
    'application': True,

}
# Timesheet_Group1

* Add lines Odoo Config
    ```conf
    workers = 5
    server_wide_modules = web, queue_job
    max_cron_threads=1
    [queue_job]
    channels = root:2

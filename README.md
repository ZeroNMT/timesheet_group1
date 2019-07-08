# Timesheet_Group1

* Thêm thuộc tính readonly cho project name và task name trong wizard/edit_task.py
    ```python
    project_name = fields.Char(readonly=True)
    task_name = fields.Char(readonly=True)
    ```
* Thêm trigger Update Timesheet Trigger trong views/timesheet_trigger.xml
    ```xml
    <record id="Update_timesheet_trigger" model="ir.cron">
        <field name="name">Update Timesheet Trigger</field>
        <field name="model_id" ref="model_account_analytic_line"/>
        <field name="state">code</field>
        <field name="code">model.update_timesheet_trigger()</field>
        <field name='interval_number'>2</field>
        <field name='interval_type'>hours</field>
        <field name="numbercall">-1</field>
    </record>
* Hàm xử lý trigger Update Timesheet Trigger được thêm trong file models/timesheet_line.py
    ```python
    @api.model
    def update_timesheet_trigger(self):
        print("Khangcero")
        # Update from Jira to Odoo(Schedual: 2 hours)
* Tạo static/src/xml/grid_view.xml để thêm một nút button Update vào Grid View
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <templates>
        <t t-name="grid.GridArrows">
            <div>
                <button t-if="widget.allowCreate" class="btn btn-primary o_grid_button_add" type="button">
                    Add a Line
                </button>
                <button t-if="widget.allowCreate" class="btn btn-primary o_grid_button_update" type="button">
                    Update
                </button>
                <button class="grid_arrow_previous btn btn-primary d-none"
                        type="button">
                    <span class="fa fa-arrow-left" role="img" aria-label="Previous" title="Previous"/>
                </button>
                <button class="btn btn-primary grid_button_initial d-none" type="button">
                    Today
                </button>
                <button class="grid_arrow_next btn btn-primary d-none"
                        type="button">
                    <span class="fa fa-arrow-right" role="img" aria-label="Next" title="Next"/>
                </button>
                <div t-if="widget._ranges.length > 1" class="btn-group">
                    <button t-foreach="widget._ranges" t-as="range"
                            class="grid_arrow_range btn btn-secondary"
                            type="button" t-att-data-name="range.name">
                        <t t-esc="range.string"/>
                    </button>
                </div>
            </div>
        </t>
    </templates>
* Thêm sự kiện xử lý button Update trong static/src/js/grid_controllers.js
    ```javascript
      renderButtons: function ($node) {
            this._super.apply(this, arguments);
            this.$buttons.on('click', '.o_grid_button_update', this._onUpdate.bind(this));
      },
      _onUpdate: function(){
            this.do_action({
                type: 'ir.actions.act_window',
                name: "Are you sure?",
                res_model: 'update.task',
                views: [
                    // [false, 'list'],
                    [false, 'form']
                ],
                target: 'new'
            });
      }  
    

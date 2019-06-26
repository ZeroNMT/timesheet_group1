# Timesheet_Group1

* Thêm sự kiện click cell trong hàm GridController
    ```js
    events: {
        'click .o_grid_input': 'func',
    },
    ```
* Tạo hàm func
    ```js
    func: function(e){
        new dialogs.FormViewDialog(this, {
            res_model: 'edit.task',
            res_id: false,
            title: _t("Update TimeSheet"),
            disable_multiple_selection: true,
            on_saved: this.reload.bind(this, {}),
        }).open();
    }
    ```
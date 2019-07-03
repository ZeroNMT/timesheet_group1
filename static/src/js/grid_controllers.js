// var utils = require('web.utils');
odoo.define('timesheet_group1.GridRender', function (require) {
    "use strict";
    var utils = require('web.utils');
    var GridController = require('web_grid.GridController');
    GridController.include({
        events: _.extend({}, GridController.prototype.events, {
        'click .o_grid_input': 'func',
        }),
        func: function(e){
            if(this.displayName === "Jira's Timesheet"){
                var ctx = _.extend({}, this.context);
                var $target = $(e.target);
                var cell_path = $target.parent().attr('data-path').split('.');
                var row_path = cell_path.slice(0, -3).concat(['rows'], cell_path.slice(-2, -1));
                var state = this.model.get();
                var cell = utils.into(state, cell_path);
                var row = utils.into(state, row_path);
                var task_name = row.values.task_id[1];
                var task_id = row.values.task_id[0];
                //-------------------------------------------
                var cols_path = cell_path.slice(0, -3).concat(['cols'], cell_path.slice(-1));
                var col = utils.into(state, cols_path);
                var column_value = col.values[state.colField][0] ? col.values[state.colField][0].split("/")[0] : false;
                var num = parseInt(row_path[0]);
                ctx['default_'+ "project_name"] = this.initialState[num].__label[1];
                ctx['default_'+ "task_name"] = task_name;
                ctx['default_'+ "date"] = column_value;
                ctx['default_'+ "task_id"] = task_id;
                ctx['default_'+ "project_id"] = this.initialState[num].__label[0];
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: "Edit",
                    res_model: 'edit.task',
                    views: [
                        // [false, 'list'],
                        [false, 'form']
                    ],
                    context: ctx,
                    target: 'new'
                });
            }
        }
    })
})


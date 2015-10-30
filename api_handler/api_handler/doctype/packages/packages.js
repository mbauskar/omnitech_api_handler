var modules_list = {
	"Learn":1,
	"Messages":1,
	"Notes":1,
	"To Do":1,
	"Activity":1,
	"Calendar":1,
	"File Manager":1,
	"Installer":1,
	"Omnitechapp":1
}

frappe.ui.form.on(cur_frm.doctype, {
	onload: function(frm){
		if(has_common(user_roles, ["Administrator", "System Manager"])) {
			// Setting the already allowed modules to 1
			if(frm.doc.allowed_module){
				enabled_modules = cur_frm.doc.allowed_module.split(",");
				$.each(enabled_modules, function(i, m) {
					modules_list[m] = 1
				});
			}
			$(cur_frm.fields_dict.modules_html.wrapper).empty()
			var module_area = $('<div style="min-height: 300px">')
				.appendTo(cur_frm.fields_dict.modules_html.wrapper);
			cur_frm.module_editor = new frappe.ModuleEditor(cur_frm, module_area)
		}
		if (cur_frm.doc.is_assigned == 1){
			fields = ["minimum_users", "maximum_users", "description"];
			cur_frm.toggle_enable(fields);
			$(":checkbox").prop("disabled", true)
		}
	},
	validate: function(frm){
		modules = []
		$.each(keys(modules_list), function(i, m) {
			if(modules_list[m] == 1)
				modules.push(m);
		});
		cur_frm.set_value("allowed_module", modules.toString());
		cur_frm.refresh_field("allowed_module");
		return true;
	}
});

frappe.ModuleEditor = Class.extend({
	init: function(frm, wrapper) {
		this.wrapper = $('<br><div class="row module-block-list"></div>').appendTo(wrapper);
		this.frm = frm;
		this.make();
	},
	make: function() {
		var me = this;

		$.each(keys(frappe.boot.modules), function(i, m) {
			if(m != "Api Handler"){
				checked = (in_list(keys(modules_list),m) && modules_list[m] == 1)? "checked" : ""
				html = '<div class="col-sm-3"><div class="checkbox"><label><input type="checkbox" \
				class="block-module-check" data-module="%(module)s" '+ checked +'>%(module)s</label></div></div>'
				$(repl(html, {module: m})).appendTo(me.wrapper);
			}
		});
		this.bind();
	},
	bind: function() {
		this.wrapper.on("change", ".block-module-check", function() {
			var module = $(this).attr('data-module');
			if($(this).prop("checked")) {
				// add to modules_list array and allowed_modules
				modules_list[module] = 1;
			} else {
				// me.frm.add_child("block_modules", {"module": module});
				modules_list[module] = 0;
			}
		});
	}
})

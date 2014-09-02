import sublime, sublime_plugin

from ..flow import FlowProject, panel

print('flow / load show status')

class FlowShowStatus( sublime_plugin.WindowCommand ):
    def run(self):
        view = self.window.active_view()
        panel(self.window, FlowProject.flow.get_status(), self.on_select)

    def on_select(self, index):

            #the flow file
        if index == 0:
            if FlowProject.flow.flow_file:
                self.window.open_file(FlowProject.flow.flow_file)

            #target
        if index == 1:
            self.window.run_command('flow_set_target_build')

            #debug flag
        if index == 2:
            if FlowProject.flow.build_debug:
                FlowProject.flow.build_debug = False
            else:
                FlowProject.flow.build_debug = True

            #verbose flag
        if index == 3:
            if FlowProject.flow.build_verbose:
                FlowProject.flow.build_verbose = False
            else:
                FlowProject.flow.build_verbose = True

    def is_visible(self):
        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if "source.flow" in scope or "source.haxe" in scope:
            return True
        else:
            return False
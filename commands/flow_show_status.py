import sublime, sublime_plugin

from ..flow import _flow_, panel

class FlowShowStatus( sublime_plugin.WindowCommand ):

    def run(self):

        view = self.window.active_view()
        panel(self.window, _flow_.get_status(), self.on_select)

    def on_select(self, index):
            #the flow file
        if index == 0:
            if _flow_.flow_file:
                self.window.open_file(_flow_.flow_file)

            #target
        if index == 1:
            self.window.run_command('flow_set_target_build')

            #debug flag
        if index == 2:
            if _flow_.build_debug:
                _flow_.build_debug = False
            else:
                _flow_.build_debug = True

            print("[flow] toggle build debug, now at " + str(_flow_.build_debug))

            #verbose flag
        if index == 3:
            if _flow_.build_verbose:
                _flow_.build_verbose = False
            else:
                _flow_.build_verbose = True

            print("[flow] toggle build verbose, now at " + str(_flow_.build_verbose))

            #build only flag
        if index == 4:
            if _flow_.build_only:
                _flow_.build_only = False
            else:
                _flow_.build_only = True

            print("[flow] toggle build only, now at " + str(_flow_.build_only))

    def is_visible(self):
        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if "source.flow" in scope or "source.haxe" in scope:
            return True
        else:
            return False


print("[flow] loaded show status")

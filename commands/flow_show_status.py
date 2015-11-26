import sublime, sublime_plugin


class FlowShowStatus( sublime_plugin.WindowCommand ):

    def run(self, sel_index=0):
        from ..flow import _flow_, panel

        view = self.window.active_view()
        panel(self.window, _flow_.get_status(), self.on_select, sel_index=sel_index)

    def on_select(self, index):
        from ..flow import _flow_

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

            self.run(sel_index=2)

                #need to refresh hxml, as it may differ
                #for debug builds, including the debug conditional
            _flow_.refresh_info();

            print("[flow] toggle build debug, now at " + str(_flow_.build_debug))

            #verbose flag
        if index == 3:
            if _flow_.build_verbose:
                _flow_.build_verbose = False
            else:
                _flow_.build_verbose = True

            print("[flow] toggle build verbose, now at " + str(_flow_.build_verbose))

            self.run(sel_index=3)

            #build type flag
        if index == 4:
            if _flow_.build_type == 'run':
                _flow_.build_type = 'build'
            elif _flow_.build_type == 'build':
                _flow_.build_type = 'compile'
            elif _flow_.build_type == 'compile':
                _flow_.build_type = 'launch'
            elif _flow_.build_type == 'launch':
                _flow_.build_type = 'run'

            print("[flow] switched build type: run/build/compile/launch, now at " + str(_flow_.build_type))

            self.run(sel_index=4)


    def is_visible(self):
        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if ("source.flow" in scope) or ("source.hxml" in scope) or ("source.haxe" in scope):
            return True
        else:
            return False


print("[flow] loaded show status")

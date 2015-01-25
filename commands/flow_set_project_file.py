import sublime, sublime_plugin



class FlowSetProjectFile( sublime_plugin.WindowCommand ):

    def run(self):
        from ..flow import _flow_

        view = self.window.active_view()
        _flow_.set_flow_file( view.file_name() )

    def is_visible(self):
        from ..flow import _flow_

        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if ("source.flow" in scope) or ("source.hxml" in scope):
            return True
        else:
            return False


print("[flow] loaded set project file")

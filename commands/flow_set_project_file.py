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

        if not "source.flow" in scope:
            return False
        else:
            return True


print("[flow] loaded set project file")

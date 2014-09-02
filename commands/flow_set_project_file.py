import sublime, sublime_plugin

from ..flow import FlowProject

print('flow / load set project file')

class FlowSetProjectFile( sublime_plugin.WindowCommand ):
    def run(self):
        view = self.window.active_view()
        FlowProject.flow.set_flow_file( view.file_name() )

    def is_visible(self):
        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if not "source.flow" in scope:
            return False
        else:
            return True
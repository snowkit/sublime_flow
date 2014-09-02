import sublime, sublime_plugin
import sys, os, subprocess

from ..flow import FlowProject, panel

import Default
stexec = getattr( Default , "exec" )
ExecCommand = stexec.ExecCommand
AsyncProcess = stexec.AsyncProcess


print('flow / load run build')

class FlowRunBuild( sublime_plugin.WindowCommand ):
    def run(self):
        view = self.window.active_view()

        if not FlowProject.flow.flow_file:
            self.window.run_command('flow_show_status')
            print("[flow] build : no flow file")
            return

        _cmd = "run"

        flow_cmd = [
            "haxelib", "run", "flow",
            _cmd, FlowProject.flow.target,
            "--project", FlowProject.flow.flow_file
        ]


        if FlowProject.flow.build_debug:
            flow_cmd.append('--debug')

        if FlowProject.flow.build_verbose:
            flow_cmd.append('--log')
            flow_cmd.append('3')

        print("[flow] build " + " ".join(flow_cmd))

        self.window.run_command("flow_do_build", {
            "cmd": flow_cmd
        })

class FlowDoBuild( ExecCommand ):

    def run( self, cmd = [],  shell_cmd = None, file_regex = "", line_regex = "", working_dir = "",
            encoding = None, env = {}, quiet = False, kill = False, **kwargs):

        if kill:
            if self.proc:
                self.proc.kill()
                self.proc = None
                self.append_data(None, "[Cancelled]")
            return

        if encoding is None:
            encoding = sys.getfilesystemencoding()

        self.output_view = self.window.get_output_panel("exec")
        self.debug_text = " ".join(cmd)
        self.encoding = encoding
        self.quiet = quiet
        self.proc = None

        if working_dir != "":
            os.chdir(working_dir)

        if not quiet:
            print( "Running " + " ".join(cmd) )

        sublime.status_message("Running build...")
        self.show_output_panel()

        try:
            self.proc = AsyncProcess( cmd, None, os.environ.copy(), self, **kwargs)
        except OSError as e:
            print(e)

    def show_output_panel(self):
        show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})

    def finish(self, *args, **kwargs):

        super(FlowDoBuild, self).finish(*args, **kwargs)
        output = self.output_view.substr(sublime.Region(0, self.output_view.size()))
        print(output)

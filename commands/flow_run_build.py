import sublime, sublime_plugin
import sys, os, subprocess


import Default
stexec = getattr( Default , "exec" )
ExecCommand = stexec.ExecCommand
AsyncProcess = stexec.AsyncProcess

class FlowRunBuild( sublime_plugin.WindowCommand ):
    def run(self, file_regex=""):
        from ..flow import _flow_

        view = self.window.active_view()

        if not _flow_.flow_file:
            self.window.run_command('flow_show_status')
            print("[flow] build : no flow file")
            return

        _cmd = "run"

        if _flow_.build_only:
            _cmd = "build"


        flow_build_args = [
            "haxelib", "run", "flow",
            _cmd, _flow_.target,
            "--project", _flow_.flow_file
        ]


        if _flow_.build_debug:
            flow_build_args.append('--debug')

        if _flow_.build_verbose:
            flow_build_args.append('--log')
            flow_build_args.append('3')

        print("[flow] build " + " ".join(flow_build_args))

        self.window.run_command("flow_do_build", {
            "cmd": flow_build_args,
            "file_regex" : file_regex,
            "working_dir": _flow_.get_working_dir()
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

        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)

        if working_dir != "":
            if not os.path.exists(working_dir):
                os.makedirs(working_dir)
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

        super(ExecCommand, self).finish(*args, **kwargs)
        output = self.output_view.substr(sublime.Region(0, self.output_view.size()))
        # print(output)

print("[flow] loaded run build")


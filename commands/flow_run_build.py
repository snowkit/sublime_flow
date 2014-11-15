import sublime, sublime_plugin
import sys, os, subprocess, time, signal, threading


import Default
stexec = getattr( Default , "exec" )
ExecCommand = stexec.ExecCommand
default_AsyncProcess = stexec.AsyncProcess

# Adapted from
# https://github.com/SublimeText/Issues/issues/357

# Encapsulates subprocess.Popen, forwarding stdout to a supplied
# ProcessListener (on a separate thread)
class AsyncProcess(default_AsyncProcess):
    def __init__(self, cmd, shell_cmd, env, listener,
            # "path" is an option in build systems
            path="",
            # "shell" is an options in build systems
            shell=False):

        if not shell_cmd and not cmd:
            raise ValueError("shell_cmd or cmd is required")

        if shell_cmd and not isinstance(shell_cmd, str):
            raise ValueError("shell_cmd must be a string")

        self.listener = listener
        self.killed = False

        self.start_time = time.time()

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Set temporary PATH to locate executable in cmd
        if path:
            old_path = os.environ["PATH"]
            # The user decides in the build system whether he wants to append $PATH
            # or tuck it at the front: "$PATH;C:\\new\\path", "C:\\new\\path;$PATH"
            os.environ["PATH"] = os.path.expandvars(path)

        proc_env = os.environ.copy()
        proc_env.update(env)
        for k, v in proc_env.items():
            proc_env[k] = os.path.expandvars(v)

        if shell_cmd and sys.platform == "win32":
            # Use shell=True on Windows, so shell_cmd is passed through with the correct escaping
            self.proc = subprocess.Popen(shell_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env, shell=True)
        elif shell_cmd and sys.platform == "darwin":
            # Use a login shell on OSX, otherwise the users expected env vars won't be setup
            self.proc = subprocess.Popen(["/bin/bash", "-l", "-c", shell_cmd], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env, shell=False,
                preexec_fn=os.setsid)
        elif shell_cmd and sys.platform == "linux":
            # Explicitly use /bin/bash on Linux, to keep Linux and OSX as
            # similar as possible. A login shell is explicitly not used for
            # linux, as it's not required
            self.proc = subprocess.Popen(["/bin/bash", "-c", shell_cmd], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env, shell=False,
                preexec_fn=os.setsid)
        else:
            # Old style build system, just do what it asks
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env,
                shell=shell, preexec_fn=os.setsid)

        if path:
            os.environ["PATH"] = old_path

        if self.proc.stdout:
            threading.Thread(target=self.read_stdout).start()

        if self.proc.stderr:
            threading.Thread(target=self.read_stderr).start()

    def kill(self):
        if not self.killed:
            if sys.platform == "win32":
                # terminate would not kill process opened by the shell cmd.exe, it will only kill
                # cmd.exe leaving the child running
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen("taskkill /PID " + str(self.proc.pid), startupinfo=startupinfo)
            else:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.terminate()
            self.killed = True
            self.listener = None


stexec.AsyncProcess = AsyncProcess

class FlowRunBuild( ExecCommand ):

    def run( self, cmd = [],  shell_cmd = None, file_regex = "", line_regex = "", working_dir = "",
            encoding = None, env = {}, quiet = False, kill = False, **kwargs):

        if kill:
            if self.proc:
                self.finish(self.proc)
                self.proc.kill()
                self.proc = None
                sublime.status_message("Build stopped")
            return

        from ..flow import _flow_

        view = self.window.active_view()

        if not _flow_.flow_file:
            self.window.run_command('flow_show_status')
            print("[flow] build : no flow file")
            return

        _cmd = "run"

        if _flow_.build_only:
            _cmd = "build"

        if _flow_.launch_only:
            _cmd = "launch"


        cmd = [
            "haxelib", "run", "flow",
            _cmd, _flow_.target,
            "--project", _flow_.flow_file
        ]

        working_dir = _flow_.get_working_dir()

        if _flow_.build_debug:
            cmd.append('--debug')

        if _flow_.build_verbose:
            cmd.append('--log')
            cmd.append('3')

        print("[flow] build " + " ".join(cmd))

        if encoding is None:
            encoding = sys.getfilesystemencoding()

        self.output_view = self.window.get_output_panel("exec")
        # self.debug_text = "\n"+" ".join(cmd)
        self.debug_text = ""
        self.encoding = encoding
        self.quiet = quiet
        self.proc = None

        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.settings().set("word_wrap", True)

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
            print(self.proc)
        except OSError as e:
            print(e)

    def show_output_panel(self):
        show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})

    def finish(self, proc):

        errs = self.output_view.find_all_results()

        if len(errs) != 0:
            self.append_string(proc, ("\n[ %d build errors ]\n\n") % len(errs))

        super(FlowRunBuild, self).finish(proc)


print("[flow] loaded run build")

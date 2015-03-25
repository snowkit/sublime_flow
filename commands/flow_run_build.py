import sublime, sublime_plugin
import sys, os, subprocess, time, signal, threading


import Default
stexec = getattr( Default , "exec" )
ExecCommand = stexec.ExecCommand
default_AsyncProcess = stexec.AsyncProcess


class FlowRunBuild( ExecCommand ):

    def run(self, cmd = None, shell_cmd = None, file_regex = "", line_regex = "", working_dir = "",
            encoding = "utf-8", env = {}, quiet = False, kill = False,
            word_wrap = True, syntax = "Packages/Text/Plain text.tmLanguage",
            # Catches "path" and "shell"
            **kwargs):

        try:
            if self.proc and not kill:
                self.proc.kill()
                self.proc = None
        except AttributeError as e:
            pass

        if kill:
            if self.proc:
                self.proc.kill()
                self.finish(self.proc)
                self.proc = None
                sublime.status_message("Build stopped")

            return

        from ..flow import _flow_

        if not _flow_.flow_file:
            self.window.run_command('flow_show_status')
            print("[flow] build : no flow file")
            return

        cmd = []
        if _flow_.flow_type is "flow":
            cmd = self.cmds_for_flow(_flow_);
        elif _flow_.flow_type is "hxml":
            cmd = self.cmds_for_haxe(_flow_);

        working_dir = _flow_.get_working_dir()

        print("[flow] build " + " ".join(cmd))

        syntax = "Packages/sublime_flow/flow-build-output.tmLanguage"

        super(FlowRunBuild, self).run(cmd, None, file_regex, line_regex, working_dir, encoding, env, True, kill, word_wrap, syntax, **kwargs)

    def is_enabled(self, kill = False):
        return True

        #override the internal one to preprocess the output,
        #what we do in this case is if absolute-path is defined
        #for haxe output, we simply strip the project path away
        #so that project local files are relative
    def append_string(self, proc, val):

        from ..flow import _flow_

        project_path = os.path.dirname(_flow_.flow_file)
        project_path = os.path.join(project_path,'') #ensure trailing slash
        val = val.replace(project_path, '')

        #:todo: we can process the paths with regex in the shared
        # plugin code and be able to jump to locations I bet

        super(FlowRunBuild, self).append_string(proc, val)

    def cmds_for_flow(self,_flow_):

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

        if _flow_.build_debug:
            cmd.append('--debug')

        if _flow_.build_verbose:
            cmd.append('--log')
            cmd.append('3')

        return cmd;

    def cmds_for_haxe(self,_flow_):
        cmd = [
            "haxe", _flow_.flow_file
        ]

        return cmd;


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

            preexec = None
            if sys.platform != "win32":
                preexec = os.setsid

            # Old style build system, just do what it asks
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env,
                shell=shell, preexec_fn=preexec)

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


print("[flow] loaded run build")

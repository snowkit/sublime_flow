# -*- coding: utf-8 -*-

import sys, os, subprocess, shutil, json, codecs, time

import sublime, sublime_plugin
from .haxe_parse_completion_list import *

#plugin location
plugin_file = __file__
plugin_filepath = os.path.realpath(plugin_file)
plugin_path = os.path.dirname(plugin_filepath)

try:
  STARTUP_INFO = subprocess.STARTUPINFO()
  STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
  STARTUP_INFO.wShowWindow = subprocess.SW_HIDE
except (AttributeError):
    STARTUP_INFO = None



_flow_ = None



class FlowProject( sublime_plugin.EventListener ):

    def __init__(self):
        global _flow_
        _flow_ = self
        print(_flow_)

        self.flow_path = "flow"
        self.flow_file = ""
        self.target = ""
        self.info_json = None
        self.completion_data = None
        self.completion_pending = False

        self.system = self.get_system()
        self.target = self.system
        self.build_debug = False
        self.build_verbose = False
        self.build_only = False

    def set_flow_file( self, file_name ):
        print("[flow] set flow file to " + file_name)
        sublime.status_message('set flow file to ' + file_name)

        self.flow_file = file_name
        self.refresh_info()

    def set_flow_target_by_index( self, index ):
        _targets = self.get_targets()
        _target = _targets[index]
        self.target = _target[0].lower()
        print("[flow] set build target to " + self.target)

        self.refresh_info()

    def refresh_info(self):
        print("[flow] refresh info/hxml on " + self.flow_file)

        self.info_json_src = run_process([
            "haxelib", "run", "flow",
            "info", self.target,
            "--project", self.flow_file
        ]).decode("utf-8");

        if self.info_json_src:
            self.info_json = json.loads(self.info_json_src)
            if not self.info_json:
                print("[flow] refresh info/hxml failed! info_json was null")
        else:
            print("[flow] refresh info/hxml failed! info_json_src was not returned from haxelib run flow, is your flow up to date?")

    def on_query_completions(self, view, prefix, locations):

        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))

        if "source.haxe" not in scope:
            return

        _res = self.completion(view, view.file_name())

        if _res is None:
            #explicitly no completion
            return ([], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        else:
            if(len(_res)):
                return (_res, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def completion(self, view, fname):

        if self.flow_file == "" or self.flow_file is None:
            sublime.status_message("No flow file, right click in a flow file! {}".format(str(self.flow_file)))
            return []

        if not self.info_json:
            sublime.status_message("no info/hxml for flow file, caching...")
            self.refresh_info()

        sel = view.sel()[0]
        word = view.word(sel)

        if len(word) == 0:
            return []

        ch = view.substr(word)[0]
        code = view.substr(sublime.Region(0, view.size()))
        prior = code[0:sel.begin()].encode('utf-8')
        offset = len(prior)

        cwd = self.get_working_dir()
        filename = fname

        if ch == "." or ch == "(":

            from sublime_haxe_completion.haxe_completion import _completionist_

            self.completion_file = fname
            self.completion_view = view
            self.completion_data = None

            _hxml = self.info_json['hxml'].splitlines()

            self.completion_pending = True

            self.completion_start_time = time.time()

            self.save_file_for_completion(view, fname)

            result = _completionist_.complete(cwd, filename, offset, _hxml)

            self.restore_file_post_completion()

            time_diff = time.time() - self.completion_start_time
            print("[flow] completion took {}".format(time_diff))

            return haxe_parse_completion_list(result)

        return []

    def save_file_for_completion( self, view, fname ):

        folder = os.path.dirname(fname)
        filename = os.path.basename( fname )
        temp_file = os.path.join( folder , "." + filename + ".tmp" )

        if os.path.exists( fname ):
            shutil.copy2( fname , temp_file )

        code = view.substr(sublime.Region(0, view.size()))
        f = codecs.open( fname , "wb" , "utf-8" , "ignore" )
        f.write( code )
        f.close()

        print("saved file for completion")

    def restore_file_post_completion( self ):

        print("restore file post completion")

        view = self.completion_view
        fname = self.completion_file
        folder = os.path.dirname( fname )
        filename = os.path.basename( fname )
        temp_file = os.path.join( folder , "." + filename + ".tmp" )

        if os.path.exists( temp_file ) :
            # print("do restore!")
            shutil.copy2( temp_file , fname )
            os.remove( temp_file )
        # else:
            # os.remove( fname )

    def on_post_save_async(self, view):
        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))
        fname = view.file_name()

        if "source.flow" in scope:
            if fname == self.flow_file:
                self.refresh_info()


    def get_working_dir(self):
        cwd = os.path.dirname(self.flow_file)
        cwd = os.path.normpath( cwd )

        return cwd

    def get_status(self):

        _result = []

        if self.flow_file:
            _result.append(['flow file', self.flow_file])
        else:
            _result.append(['no flow file', 'specify a flow file first'])
            return _result

        if self.target:
            _result.append(['flow target', self.target])
        else:
            _result.append(['flow target', self.system])

        _result.append(['Toggle debug build', "currently debug : " + str(self.build_debug).lower() ])
        _result.append(['Toggle verbose build', "currently verbose : " + str(self.build_verbose).lower() ])
        _result.append(['Toggle build only', "currently build only : " + str(self.build_only).lower() ])

        return _result

    def get_system(self):

        _result = ""
        _system = sys.platform

        if _system == "win32" or _system == "cygwin":
            _result = "windows"
        elif _system == "darwin":
            _result = "mac"
        else:
            _system = "linux"

        return _result


    def get_targets(self):

        _result = []

        if not self.flow_file:
            return _result

        _result.append(['Mac', 'desktop, native mac app'])
        _result.append(['Linux', 'desktop, native linux app'])
        _result.append(['Windows', 'desktop, native windows app'])
        _result.append(['Android', 'mobile, native android app'])
        _result.append(['iOS', 'mobile, native ios project'])
        _result.append(['Web', 'web, web based app'])

        _invalid = self.info_json['targets_invalid']

        _result[:] = [_item for _item in _result if not _item[0].lower() in _invalid ]

        _result.insert(0, ['unavailable from ' + self.system, ", ".join(_invalid) ])

        return _result



def run_process( args ):
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=STARTUP_INFO).communicate()[0]

def panel(_window, options, done, flags=0, sel_index=0, on_highlighted=None):
    sublime.set_timeout(lambda: _window.show_quick_panel(options, done, flags, sel_index, on_highlighted), 10)

# http://stackoverflow.com/a/10863489/2503795
class ChainedActionsCommand(sublime_plugin.TextCommand):
    def run(self, edit, actions, args):
        for i, action in enumerate(actions):
            self.view.run_command(action, args[i])

#force reload

def force_reload():
    modules_to_load = [
        'sublime_flow.commands.flow_set_project_file',
        'sublime_flow.commands.flow_set_target_build',
        'sublime_flow.commands.flow_show_status',
        'sublime_flow.commands.flow_run_build',
        'sublime_flow.commands.haxe_generate_import',
        'sublime_flow.haxe_parse_completion_list'
    ]

    import imp
    for mod in modules_to_load:
        if sys.modules.get(mod,None) != None:
            try:
                # print("reload " + mod)
                imp.reload(sys.modules[mod])
            except:
                pass

from .commands.flow_show_status import FlowShowStatus
from .commands.flow_set_target_build import FlowSetTargetBuild
from .commands.flow_set_project_file import FlowSetProjectFile
from .commands.flow_run_build import FlowDoBuild, FlowRunBuild
from .commands.haxe_generate_import import HaxeGenerateImport

force_reload()

from .commands.flow_show_status import FlowShowStatus
from .commands.flow_set_target_build import FlowSetTargetBuild
from .commands.flow_set_project_file import FlowSetProjectFile
from .commands.flow_run_build import FlowDoBuild, FlowRunBuild
from .commands.haxe_generate_import import HaxeGenerateImport
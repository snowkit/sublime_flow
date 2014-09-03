# -*- coding: utf-8 -*-

import sys, os, subprocess, shutil, json

import sublime, sublime_plugin
from .haxe_parse_completion_list import *

#plugin location
plugin_file = __file__
plugin_filepath = os.path.realpath(plugin_file)
plugin_path = os.path.dirname(plugin_filepath)


def run_process( args ):
    startupinfo = None
    #startupinfo = subprocess.STARTUPINFO()
    #startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.Popen(args, stdout=subprocess.PIPE, startupinfo=startupinfo).communicate()[0]

def panel(_window, options, done, flags=0, sel_index=0, on_highlighted=None):
    sublime.set_timeout(lambda: _window.show_quick_panel(options, done, flags, sel_index, on_highlighted), 10)


class FlowCompletionCallbackCommand( sublime_plugin.WindowCommand  ):

    def run( self, result=None, **kwargs ) :
        FlowProject.flow.on_completion(result)




class FlowProject( sublime_plugin.EventListener ):

    def __init__(self):
        FlowProject.flow = self

        self.flow_path = "flow"
        self.flow_file = ""
        self.target = ""
        self.info_json = None
        self.completion_data = None

        self.system = self.get_system()
        self.target = self.system
        self.build_debug = False
        self.build_verbose = False
        self.build_only = False

    def __del__(self):
        print("[flow] __del__")
        FlowProject.flow = None
        self.flow_file = None
        self.flow_path = None
        self.info_json = None
        del FlowProject.flow
        del self


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

    def on_query_completions(self, view, prefix, locations):

        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))

        if "comment" in scope:
            return []

        if self.completion_data is not None:
            return self.parse_completion_data()

        return []

    def parse_completion_data(self):
        if self.completion_data is None:
            return []

        res = haxe_parse_completion_list(self.completion_data)
        # print(res)

        self.completion_data = None

        return res

    def completion(self, view, fname):

        if self.flow_file == "" or self.flow_file is None:
            sublime.status_message("No flow file, right click in a flow file!")
            return

        if not self.info_json:
            sublime.status_message("no info/hxml for flow file, caching...")
            self.refresh_info()

        sel = view.sel()[0]
        word = view.word(sel)

        if len(word) == 0:
            return

        ch = view.substr(word)[0]
        offset = sel.begin()
        line, column = view.rowcol(offset)
        cwd = self.get_working_dir()
        filename = fname

        if ch == "." or ch == "(":

            print("[flow] start completion in " + cwd)

            self.save_file_for_completion(view, fname)
            self.completion_file = fname
            self.completion_view = view
            self.completion_data = None

            view.window().run_command('haxe_completion_complete', {
                "on_complete":'flow_completion_callback',
                "cwd":cwd,
                "fname":filename,
                "offset":offset,
                "hxml":self.info_json['hxml'].splitlines()
            })

    def save_file_for_completion( self, view, fname ):

        folder = os.path.dirname(fname)
        filename = os.path.basename( fname )
        temp_file = os.path.join( folder , filename + ".tmp" )

        if os.path.exists( fname ):
            shutil.copy2( fname , temp_file )

        view.run_command("save")

    def restore_file_post_completion( self ):

        fname = self.completion_file
        folder = os.path.dirname( fname )
        filename = os.path.basename( fname )
        temp_file = os.path.join( folder , filename + ".tmp" )

        if os.path.exists( temp_file ) :
            os.remove( temp_file )
        else:
            os.remove( fname )

    def on_completion(self, result):

        view = self.completion_view
        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))

        if "source.haxe" not in scope:
            return

        self.completion_data = result

            #this forces on_query_completion
        view.run_command( "auto_complete" , {
            "api_completions_only" : True,
            "disable_auto_insert" : True,
            "next_completion_if_showing" : False
        })

        self.restore_file_post_completion()

        self.completion_file = None
        self.completion_view = None

    def on_post_save_async(self, view):
        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))

        if "source.flow" in scope:
            if fname == self.flow_file:
                self.refresh_info()

        #when changing a flow file that is set as the active project,
        #we automatically refresh the hxml so that the completion is reliable
    def on_modified_async(self, view):
        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))
        fname = view.file_name()

        if "source.haxe" in scope:
            fname = view.file_name()
            self.completion(view, fname)

    def get_working_dir(self):
        cwd = os.path.dirname(self.flow_file)
        cwd = os.path.join( cwd, self.info_json['paths']['build'] )

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

print("[flow] hello flow")
from .commands import *


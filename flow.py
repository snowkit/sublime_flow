# -*- coding: utf-8 -*-

import sys, os, subprocess, codecs, shutil

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



class FlowCompletionCallbackCommand( sublime_plugin.WindowCommand  ):

    def run( self, result=None, **kwargs ) :
        FlowProject.flow.on_completion(result)




class FlowProject( sublime_plugin.EventListener ):

    def __init__(self):
        FlowProject.flow = self

        self.flow_path = "flow"
        self.flow_file = ""
        self.hxml = ""
        self.completion_data = None

    def __del__(self):
        print("[flow] __del__")
        FlowProject.flow = None
        self.flow_file = None
        self.flow_path = None
        self.hxml = None
        del FlowProject.flow
        del self

    def set_flow_file( self, file_name ):
        print("[flow] set flow file to " + file_name)
        sublime.status_message('set flow file to ' + file_name)
        self.flow_file = file_name
        self.refresh_hxml()


    def refresh_hxml(self):
        print("[flow] refresh hxml on " + self.flow_file)

        self.hxml = run_process([
            self.flow_path,
            "info",
            "--hxml",
            "--project", self.flow_file
        ]).decode("utf-8");

    def on_query_completions(self, view, prefix, locations):

        if self.completion_data is not None:
            return self.parse_completion_data()

        return []

    def parse_completion_data(self):
        if self.completion_data is None:
            return []

        res = haxe_parse_completion_list(self.completion_data)
        print(res)

        self.completion_data = None

        return res

    def completion(self, view, fname):

        if self.flow_file == "" or self.flow_file is None:
            sublime.status_message("No flow file, right click in a flow file!")
            return

        if self.hxml == "" or self.hxml == None:
            sublime.status_message("no hxml for flow file, caching...")
            self.refresh_hxml()

        sel = view.sel()[0]
        word = view.word(sel)

        if len(word) == 0:
            return

        ch = view.substr(word)[0]
        offset = sel.begin()
        line, column = view.rowcol(offset)
        cwd = os.path.dirname(self.flow_file)
        filename = fname #os.path.basename(fname)
        cwd += "/bin/mac64.build/"

        if ch == "." or ch == "(":

            print("[flow] start completion")

            self.save_file_for_completion(view, fname)
            self.completion_file = fname
            self.completion_view = view
            self.completion_data = None

            view.window().run_command('haxe_completion_complete', {
                "on_complete":'flow_completion_callback',
                "cwd":cwd,
                "fname":filename,
                "offset":offset,
                "hxml":self.hxml.splitlines()
            })

    def save_file_for_completion( self, view, fname ):

        folder = os.path.dirname(fname)
        filename = os.path.basename( fname )
        temp_file = os.path.join( folder , filename + ".tmp" )

        if os.path.exists( fname ):
            shutil.copy2( fname , temp_file )

        code = view.substr(sublime.Region(0, view.size()))
        f = codecs.open( fname , "wb" , "utf-8" , "ignore" )
        f.write( code )
        f.close()

    def restore_file_post_completion( self ):

        fname = self.completion_file
        folder = os.path.dirname( fname )
        filename = os.path.basename( fname )
        temp_file = os.path.join( folder , filename + ".tmp" )

        if os.path.exists( temp_file ) :
            shutil.copy2( temp_file , fname )
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

        #when changing a flow file that is set as the active project,
        #we automatically refresh the hxml so that the completion is reliable
    def on_modified_async(self, view):
        pt = view.sel()[0].b
        scope = str(view.scope_name(pt))
        fname = view.file_name()

        if "source.flow" in scope:
            if fname == self.flow_file:
                self.refresh_hxml()

        elif "source.haxe" in scope:
            fname = view.file_name()
            self.completion(view, fname)



print("hello flow")
from .commands import *


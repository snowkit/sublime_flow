
import sublime, sublime_plugin
import xml.etree.ElementTree as ET

def haxe_has_error(_list):

    try:

        root = ET.fromstring(str(_list))
        return False

    except ET.ParseError as e:

        return _list.splitlines()

def haxe_has_args(_list):

    root = ET.fromstring(str(_list))
    
    if root.tag == 'type':
        return parse_type(root.text.strip())

    return None

def haxe_completion_list(_list):

    if _list is None:
        return None
    
    root = ET.fromstring(str(_list))

        #list is completion of properties/methods on an object/Type
    if root.tag == 'list':

        members = []

        for node in root:

            _name = node.attrib['n']
            _type = node.find('t').text

            if _type is None:
                if _name[0].islower():
                    _type = "package"
                else:
                    _type = _name

            if is_function(_type):
                _a, _ret = parse_args(_type)
                if(_ret.find('Unknown') != -1):
                    _ret = ' '
                members.append( ( 'm· ' + _name+'\t'+_ret, _name ) )
            else:
                members.append( ( 'p· ' + _name+'\t'+_type, _name ) )

        if len(members):
            return members
        else:
            return [('No members/properties', '')]

    return None

#returns args, return_type from a <type> string
def parse_args(_type):
    _tmp = _type

    _args = []
    _result = 0
    _count = 0
    while _result != None:
        _result = _tmp.find(' -> ')
        _arg = _tmp[:_result]

            #found a () which means it's a function type
        _end = ')'
        _par = _arg.find('(')
        if(_par == -1):
            _par = _arg.find('<')
            _end = '> ->'

        if _par != -1:
            _endpar = _tmp.find(_end)
            _arg = _tmp[:_endpar+1]
            _tmp = _tmp[_endpar+1:]
        else :
            _tmp = _tmp[_result+4:]

        if _arg:
            _args.append(_arg)

        _result = _tmp.find(' -> ')

        _count += 1
        if _count > 10 or _result == -1:
            _result = None

    return _args, _tmp

#returns a single tuple parsed for legibility as function args, clamped if too long etc
def parse_type(_type):

    if _type is None:
        return None

    if _type == "":
        return []

    _args = []

    if _type.find(':') == -1 and _type.find('->') == -1:
        _args = [ _type.strip() ]
    else:
        _args, _return = parse_args(_type)

    if len(_args) == 1:
        if _args[0] in ['Void', 'Dynamic']:
            return []

    _list = []

    for item in _args:
        node = item.split(':')
        _name = node[0]
        _typename = "Unknown"

        if len(node) > 1:
            _typename = node[1]

        _list.append(sanitize(_name) + ':' + sanitize(_typename))

    return ', '.join(_list)

def sanitize(_str):
    _str = _str.replace('>','&gt;')
    _str = _str.replace('<','&lt;')
    return _str


#returns True if the string is completion info for a function
def is_function(_str):
    if _str:
        return _str.find(' -> ') != -1
    else:
        return False

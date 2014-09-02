
import xml.etree.ElementTree as ET

def haxe_parse_completion_list(_list):

    if _list is None:
        return []

    print(_list)

    try:
        root = ET.fromstring(str(_list))
    except ET.ParseError as e:
        #if there was a parse error, this is an error from haxe,
        #so we will show it for now as a completion with blank insert
        _error = _list.split('\n')
        return [(_error[0], '')]

        #list is completion of properties/methods on an object/Type
    if root.tag == 'list':

        members = []

        for node in root:

            _name = node.attrib['n']
            _type = node.find('t').text

            if _type is None:
                _type = "-"

            if is_function(_type):
                members.append( ( _name+'\tfunction', _name ) )
            else:
                members.append( ( _name+'\t'+_type, _name ) )

        return members

        #type is function arguments and the like
    elif root.tag == 'type':

        args = []

        parsed = parse_type(root.text.strip())
        if parsed is not None:
            args = parsed

        return args

    return []

#returns a single tuple parsed for legibility as function args, clamped if too long etc
def parse_type(_type):

    if _type is None:
        return None

    if _type == "":
        return []

    _list = _type.split(' -> ')

        #removes the return type
    _list.pop()

    result = []

    for item in _list:
        print(item)
        node = item.split(' : ')
        print(node)
        _name = node[0]
        _type = node[1]
        result.append((_name+'\t'+_type, _name))

    return result

#returns True if the string is completion info for a function
def is_function(_str):
    if _str:
        return _str.find(' -> ') != -1
    else:
        return False

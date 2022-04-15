"""
Library for parsing a library table file (e.g. used for project-specific library settings files).
"""

import re
from typing import List


class LibTableEntry:
    def __init__(self, name: str, type: str, uri: str, opt: str, desc: str):
        self.name: str = name
        self.type: str = type
        self.uri: str = uri
        self.opt: str = opt
        self.desc: str = desc

class LibTable:

    def __init__(self, filename: str):

        RE_NAME: str = r'\(name "?([^\)"]*)"?\)'
        RE_TYPE: str = r'\(type "?([^\)"]*)"?\)'
        RE_URI: str = r'\(uri "?([^\)"]*)"?\)'
        RE_OPT: str = r'\(options "?([^\)"]*)"?\)'
        RE_DESC: str = r'\(descr "?([^\)"]*)"?'

        self.entries: List[LibTableEntry] = []
        self.errors: List[str] = []

        with open(filename, "r") as lib_table_file:

            for line in lib_table_file:

                # Skip lines that do not define a library
                if "(lib " not in line:
                    continue

                re_name = re.search(RE_NAME, line)
                re_type = re.search(RE_TYPE, line)
                re_uri = re.search(RE_URI, line)
                re_opt = re.search(RE_OPT, line)
                re_desc = re.search(RE_DESC, line)

                if re_name and re_type and re_uri and re_opt and re_desc:
                    name = re_name.groups()[0]
                    type = re_type.groups()[0]
                    uri = re_uri.groups()[0]
                    opt = re_opt.groups()[0]
                    desc = re_desc.groups()[0]
                    entry = LibTableEntry(name=name, type=type, uri=uri, opt=opt, desc=desc)

                    self.entries.append(entry)
                else:
                    self.errors.append(line)

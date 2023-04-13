#!/usr/bin/python3
# -*- coding: utf-8 -*-
from sploitkit.__info__ import __author__, __copyright__, __email__, __license__, __version__
from tinyscript import *


__name__      = "__main__"
__script__    = "sploitkit"
__examples__  = ["my-sploit", "my-sploit -s"]
__doc__       = """
This tool allows to quickly create a new Sploitkit project.
"""


MAIN = """#!/usr/bin/python3
from sploitkit import FrameworkConsole
from tinyscript import *


class MySploitConsole(FrameworkConsole):
    #TODO: set your console attributes
    pass


if __name__ == '__main__':
    parser.add_argument("-d", "--dev", action="store_true", help="enable development mode")
    parser.add_argument("-r", "--rcfile", type=ts.file_exists, help="execute commands from a rcfile")
    initialize(exit_at_interrupt=False)
    c = MySploitConsole(
        "MySploit",
        #TODO: configure your console settings
        dev=args.dev,
        debug=args.verbose,
    )
    c.rcfile(args.rcfile) if args.rcfile else c.start()
"""
COMMANDS = """from sploitkit import *


class CommandWithOneArg(Command):
    \""" Description here \"""
    level = "module"
    single_arg = True

    def complete_values(self):
        #TODO: compute the list of possible values
        return []

    def run(self):
        #TODO: compute results here
        pass

    def validate(self, value):
        #TODO: validate the input value
        if value not in self.complete_values():
            raise ValueError("invalid value")


class CommandWithTwoArgs(Command):
    \""" Description here \"""
    level = "module"

    def complete_keys(self):
        #TODO: compute the list of possible keys
        return []

    def complete_values(self, key=None):
        #TODO: compute the list of possible values taking the key into account
        return []

    def run(self):
        #TODO: compute results here
        pass
"""
MODULES = """from sploitkit import *


class MyFirstModule(Module):
    \""" Description here 

    Author:  your name (your email)
    Version: 1.0
    \"""
    def run(self):
        pass


class MySecondModule(Module):
    \""" Description here 

    Author:  your name (your email)
    Version: 1.0
    \"""
    def run(self):
        pass
"""


PROJECT_STRUCTURE = {
    'README': "# {}\n\n#TODO: Fill in the README",
    'main.py': MAIN,
    'requirements.txt': None,
    'banners': {},
    'commands': {'commands.py': COMMANDS},
    'modules': {'modules.py': MODULES},
}


def main():
    parser.add_argument("name", help="project name")
    parser.add_argument("-s", "--show-todo", dest="todo", action="store_true", help="show the TODO list")
    initialize(noargs_action="wizard")
    p = ts.ProjectPath(args.name, PROJECT_STRUCTURE)
    if args.todo:
        for k, v in p.todo.items():
            print("- [%s] %s" % (k, v))


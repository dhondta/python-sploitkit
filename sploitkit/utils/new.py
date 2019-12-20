#!/usr/bin/env python
from tinyscript import *

from sploitkit.utils.path import Path


COMMANDS = """
from sploitkit import *


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
MAIN = """
#!/usr/bin/python3
from sploitkit import FrameworkConsole


class MySploitConsole(FrameworkConsole):
    #TODO: set your console attributes
    pass


if __name__ == '__main__':
    MySploitConsole(
        "MySploit",
        #TODO: configure your console settings
    ).start()
"""
MODULE = """
from sploitkit import *


class MyFirstModule(Module):
    \""" Description here 

    Author:  your name (your email)
    Version: 1.0
    \"""
    def run(self):
        pass
"""
README = """
# {}

#TODO: Fill in the README
"""


def create_project(name):
    """ Create a project folder with its base files.

    :param name: folder name for the project
    """
    new = Path(name)
    if new.exists():
        return
    new.mkdir()
    new.joinpath("README").append_text(README.strip())
    new.joinpath("main.py").append_text(MAIN.strip())
    new.joinpath("requirements.txt").touch()
    new.joinpath("banners").mkdir(exist_ok=True)
    d = new.joinpath("commands")
    d.mkdir(exist_ok=True)
    d.joinpath("template.py").append_text(COMMANDS.strip())
    d = new.joinpath("modules")
    d.mkdir(exist_ok=True)
    d.joinpath("template.py").append_text(MODULE.strip())


def show_todo(folder):
    """ Walk the given folder and display TODO statements from the walked files.

    :param folder: folder to be walked through
    """
    MARKER = "#TODO:"
    logger.info("TODO list:")
    for root, dirs, files in os.walk(folder):
        for fn in files:
            fp = os.path.join(root, fn)
            current_cls, line_number = None, None
            with open(fp) as f:
                for i, l in enumerate(f):
                    if "class " in l:
                        current_cls = l.split("class ")[1].split("(")[0].strip()
                    if "def " in l:
                        line_number = str(i + 1)
                    if MARKER in l:
                        s = "- [{}] "
                        m = str(Path(fp).child)
                        if current_cls is not None:
                            m += ":" + current_cls
                        m += ":" + (line_number or str(i + 1))
                        s = s.format(m)
                        s += l.split(MARKER, 1)[1].strip()
                        print(s)

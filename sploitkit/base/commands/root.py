# -*- coding: UTF-8 -*-
import shlex
from sploitkit import *


# ----------------------- GENERAL-PURPOSE ROOT-LEVEL COMMANDS ------------------
class Help(Command):
    """ Display help (commands or individual command/module) """
    level = "root"
    keys  = ["command"]
    
    def __init__(self):
        if len(Module.modules) > 0 and "module" not in self.keys:
            self.keys += ["module"]
    
    def complete_values(self, key):
        if key == "command":
            return self.console.commands.keys()
        elif key == "module":
            return sorted([x.fullpath for x in Module.subclasses])
    
    def run(self, key=None, value=None):
        if key is None:
            print_formatted_text(Command.get_help())
        elif key == "command":
            print_formatted_text(self.console.commands[value].help(value))
        elif key == "module":
            print_formatted_text(self.modules[value].help)
    
    def validate(self, key=None, value=None):
        if key is None and value is None:
            return
        super(Help, self).validate(key, value)

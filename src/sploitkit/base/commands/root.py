# -*- coding: UTF-8 -*-
from sploitkit import *


# ----------------------- GENERAL-PURPOSE ROOT-LEVEL COMMANDS ------------------
class Help(Command):
    """ Display help (commands or individual command/module) """
    level = "root"
    keys  = ["command"]
    
    def __init__(self):
        if len(Module.modules) > 0 and "module" not in self.keys:
            self.keys += ["module"]
    
    def complete_values(self, category):
        if category == "command":
            return self.console.commands.keys()
        elif category == "module":
            return sorted([x.fullpath for x in Module.subclasses])
    
    def run(self, category=None, value=None):
        if category is None:
            print_formatted_text(Command.get_help(except_levels="module"))
        elif category == "command":
            print_formatted_text(self.console.commands[value].help(value))
        elif category == "module":
            print_formatted_text(self.modules[value].help)
    
    def validate(self, category=None, value=None):
        if category is None and value is None:
            return
        super(Help, self).validate(category, value)


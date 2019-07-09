from __future__ import unicode_literals, print_function

import shlex
from sploitkit import *
from sploitkit.utils.objects import BorderlessTable, NameDescription, Synopsis


# ----------------------- GENERAL-PURPOSE ROOT-LEVEL COMMANDS ------------------
class Help(Command):
    """ Display help (commands or individual command/module) """
    level = "root"
    options = ["command", "module"]
    
    def __init__(self):
        if len(Console.parent.modules) > 0:
            self.options = self.options + ["module"]
    
    def complete_options(self):
        return self.options
    
    def complete_values(self, option):
        if option == "command":
            return Console.parent.commands.keys()
        elif option == "module":
            return sorted([x.fullpath for x in Module.subclasses])
    
    def run(self, option=None, value=None):
        if option is None:
            print_formatted_text(Command.get_help(*self.levels))
        elif option == "command":
            print_formatted_text(Console.parent.commands[value].help(value))
        elif option == "module":
            print_formatted_text(Console.parent.modules.rget(value).help)
    
    def validate(self, option=None, value=None):
        assert option is None or option in self.options, \
            "Please enter help [{}] ...".format('|'.join(self.options))
        if option == "command":
            assert value in Console.parent.commands.keys(), \
                "Please enter a valid command"
        elif option == "module":
            assert value in [x.fullpath for x in Module.subclasses], \
                "Please enter a valid module"

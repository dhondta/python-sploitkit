from __future__ import unicode_literals

from sploitkit import *


# ----------------------------- SUBCONSOLE DEFINITION --------------------------
class ModuleConsole(Console):
    """ Module subconsole definition. """
    level = "module"
    message = [
        ('class:prompt', " "),
        ('class:prompt', None),
        ('class:prompt', "("),
        ('class:module', None),
        ('class:prompt', ")"),
    ]
    style = {
        'prompt': "#eeeeee",
        'module': "#ff0000",
    }
    
    def __init__(self, parent, fullpath):
        self.path = fullpath
        self.module = parent.modules.rget(fullpath)
        self.logname = fullpath
        self.message[1] = ('class:prompt', self.module.category)
        self.message[3] = ('class:module', self.module.base)
        self.config.copy(parent.config, 'WORKSPACE')
        super(ModuleConsole, self).__init__(parent)


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Use(Command):
    """ Select a module """
    def complete_values(self):
        return Module.get_list()
    
    def run(self, module):
        fullpath = Module.get_modules(module).fullpath
        cmodule = getattr(self.console, "module", None)
        # avoid starting a new subconsole for the same module
        if cmodule is not None and cmodule.fullpath == fullpath:
            return
        ModuleConsole(self.console, fullpath).start()
    
    def validate(self, value):
        if value not in self.complete_values():
            raise ValueError("'{}' does not exist".format(value))


# ----------------------------- MODULE-LEVEL COMMANDS --------------------------
class ModuleCommand(Command):
    """ Proxy class (for setting the level attribute). """
    level = "module"


class Run(ModuleCommand):
    """ Run module """
    def run(self):
        self.console.module().run()


class Show(ModuleCommand):
    """ Show module-relevant information or options """
    options = ["info", "options"]
    
    def complete_options(self):
        return self.options
    
    def complete_values(self, option):
        if option == "options":
            return self.config.keys()
    
    def run(self, option, value=None):
        if option == "options" and value is None:
            data = [["Option", "Value"]]
            for k, v in sorted(self.config.items(), key=lambda x: x[0]):
                data.append([k, v])
            print_formatted_text(BorderlessTable(data, "Console options"))
        elif option == "options":
            print_formatted_text(NameDescription(option, self.config[option]))
        elif option == "info":
            i = self.console.module.info
            if len(i.strip()) != "":
                print_formatted_text(i)
    
    def validate(self, option, value=None):
        if option not in self.options:
            raise ValueError("'{}' not in options".format(option))
        elif value is not None and option == "options" and \
            value not in self.config.keys():
            raise ValueError("'{}' not in options".format(value))


"""
 Name: HackerTarget Lookup
 Path: modules/recon/domains-hosts/hackertarget.py
 Author: Michael Henriksen (@michenriksen)

Description:
 Uses the HackerTarget.com API to find host names. Updates the 'hosts' table with the results.

Options:
 Name Current Value Required Description
 ------ ------------- -------- -----------
 SOURCE default yes source of input (see 'show info' for details)

Source Options:
  default        SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL
  <string>       string representing a single input
  <path>         path to a file containing a list of inputs
  query <sql>    database query returning one column of inputs

Comments:
  * [...]
"""

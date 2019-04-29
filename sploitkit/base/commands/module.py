from __future__ import unicode_literals

from sploitkit import *


# ----------------------------- SUBCONSOLE DEFINITION --------------------------
class ModuleConsole(Console):
    level = "project"
    message = [
        ('class:prompt', " "),
        ('class:prompt', None),
        ('class:prompt', "("),
        ('class:module', None),
        ('class:prompt', ")"),
    ]
    style = {
        'prompt':  "#eeeeee",
        'project': "#0000ff",
    }
    
    def __init__(self, parent, module_fullpath):
        self.module = parent.modules.rget(module_fullpath)
        self.message[1] = ('class:prompt', self.module.category)
        self.message[3] = ('class:module', self.module.name)
        self.config['WORKSPACE'] = str(Path(parent.config['WORKSPACE']) \
                                       .joinpath(self.name))
        super(ProjectConsole, self).__init__(parent)


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Use(Command):
    """ Select a module """
    def complete_values(self, option):
        return projects(self)
    
    def run(self, module):
        m = Module.get_modules(module)
        ModuleConsole.name = m.name
        ModuleConsole.path = m.fullpath
        ModuleConsole(self.console).start()


# ----------------------------- MODULE-LEVEL COMMANDS --------------------------
class Show(Command):
    """ Show console options """
    level = "module"
    options = ["info", "options"]
    
    def complete_options(self):
        return self.options
    
    def complete_values(self, option):
        if option == "options":
            return self.options
        elif option == "info":
            return []
            #FIXME: show information e.g. like in Recon-ng (see hereafter)
    
    def run(self, option, value=None):
        if value is None:
            data = [["Option", "Value"]]
            for k, v in sorted(self.config.items(), key=lambda x: x[0]):
                data.append([k, v])
            print_formatted_text(BorderlessTable(data, "Console options"))
        else:
            print_formatted_text(NameDescription(option, self.config[option]))
    
    def validate(self, option, value=None):
        assert option in self.options


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

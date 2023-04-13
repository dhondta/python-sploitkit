# -*- coding: UTF-8 -*-
from prompt_toolkit.formatted_text import ANSI

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
    
    def __init__(self, parent, module):
        self.attach(module, True)
        self.logname = module.fullpath
        self.message[1] = ('class:prompt', self.module.category)
        self.message[3] = ('class:module', self.module.base)
        self.opt_prefix = "Module"
        super(ModuleConsole, self).__init__(parent)


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Use(Command):
    """ Select a module """
    except_levels = ["session"]
    
    def complete_values(self):
        return Module.get_list()
    
    def run(self, module):
        new_mod, old_mod = Module.get_modules(module), self.module
        # avoid starting a new subconsole for the same module
        if old_mod is not None and old_mod.fullpath == new_mod.fullpath:
            return
        ModuleConsole(self.console, new_mod).start()


# ----------------------------- MODULE-LEVEL COMMANDS --------------------------
class ModuleCommand(Command):
    """ Proxy class (for setting the level attribute). """
    level = "module"


class Run(ModuleCommand):
    """ Run module """
    def run(self):
        if self.module.check():
            self.module._instance.run()


class Show(ModuleCommand):
    """ Show module-relevant information or options """
    keys = ["info", "options"]
    
    def complete_values(self, key):
        if key == "options":
            return list(self.config.keys())
        elif key == "issues":
            l = []
            for attr in ["console", "module"]:
                for _, __, errors in getattr(self, attr).issues(self.cname):
                    l.extend(list(errors.keys()))
            return l
    
    def run(self, key, value=None):
        if key == "options":
            if value is None:
                print_formatted_text(ANSI(str(self.config)))
            else:
                c = Config()
                c[self.config.option(value), True] = self.config[value]
                print_formatted_text(ANSI(str(c)))
        elif key == "info":
            i = self.console.module.get_info(("fullpath|path", "description"), ("author", "email", "version"),
                                             ("comments",), ("options",), show_all=True)
            if len(i.strip()) != "":
                print_formatted_text(i)
        elif key == "issues":
            t = Entity.get_issues()
            if len(t) > 0:
                print_formatted_text(t)
    
    def set_keys(self):
        if self.module and self.module.has_issues(self.cname):
            self.keys += ["issues"]
        else:
            while "issues" in self.keys:
                self.keys.remove("issues")


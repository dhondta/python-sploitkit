# -*- coding: UTF-8 -*-
from prompt_toolkit.formatted_text import ANSI
from sploitkit import *
from termcolor import colored


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
        super(ModuleConsole, self).__init__(parent)


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Use(Command):
    """ Select a module """
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
    
    def __init__(self):
        if self.module and self.module.has_issues():
            self.keys = self.keys + ["issues"]
    
    def complete_values(self, key):
        if key == "options":
            return self.config.keys()
        elif key == "issues":
            l = []
            for attr in ["console", "module"]:
                for cls, subcls, errors in getattr(self, attr).get_issues():
                    l.extend(errors.keys())
            return l
    
    def run(self, key, value=None):
        if key == "options":
            data = [["Name", "Value", "Required", "Description"]]
            for n, d, v, r in sorted(self.config.items(False),
                                     key=lambda x: x[0]):
                r = ["N", "Y"][r]
                if value is None or n == value:
                    if v == "undefined":
                        n = colored(n, "red", attrs=['bold'])
                        v = colored(v, "red", attrs=['bold'])
                        r = colored(r, "red", attrs=['bold'])
                    data.append([n, v, r, d])
            t = BorderlessTable(data, "Module options")
            print_formatted_text(ANSI(t.table))
        elif key == "info":
            i = self.console.module.get_info(("fullpath|path", "description"),
                                             ("author", "email", "version"),
                                             ("comments",), ("options",),
                                             show_all=True)
            if len(i.strip()) != "":
                print_formatted_text(i)
        elif key == "issues":
            for cls, subcls, errors in self.console.module.get_issues():
                if value is None:
                    t = "{}: {}\n- ".format(cls, subcls)
                    t += "\n- ".join(m(k, e) for k, err in errors.items() \
                                             for e in err) + "\n"
                else:
                    t = ""
                    for k, e in errors.items():
                        if k == value:
                            t += "- {}/{}: {}".format(cls, subcls, e)
                print_formatted_text(t)

from __future__ import unicode_literals, print_function

import shlex
from sploitkit import *
from subprocess import call


projects = lambda c: [x.stem for x in Path(c.console.config['WORKSPACE'])\
                      .expanduser().iterpubdir()]


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Back(Command):
    """ Come back to the previous console level """
    except_levels = ["root"]
    
    def run(self):
        raise ConsoleExit


class Exit(Command):
    """ Exit the console """
    aliases = ["quit"]
       
    def run(self):
        raise SystemExit


class Help(Command):
    """ Display help """
    aliases = ["?"]
    
    def run(self):
        print_formatted_text(Command.get_help("general", self.console.level))


class Search(Command):
    """ Search for text in modules """
    splitargs = False
    
    def run(self, text):
        keywords = shlex.split(text)
        i = 0
        for m in Module.subclasses:
            for k in keywords:
                if m.search(k):
                    if i == 0:
                        d = [["Name", "Path", "Description"]]
                        d.append([m.name, m.path, m.description])
                        t = BorderlessTable(d, "Matching modules")
                        print("")
                    else:
                        d = [[m.name, m.path, m.description]]
                        t = BorderlessTable(d)
                    print(t.table)
                    i += 1
        if i == 0:
            self.logger.error("No match found")
        else:
            self.logger.debug("{} matching entr{}"
                              .format(i, ["y", "ies"][i > 1]))
            print("")


class Show(Command):
    """ Show options, projects or modules """
    level = "root"
    options = ["modules", "options", "projects"]
    
    def complete_values(self, option):
        if option == "modules":
            return [m for m in self.console.modules.keys() \
                    if getattr(m, "enabled", True)]
        elif option == "options":
            return self.config.keys()
        elif option == "projects":
            return projects(self)
    
    def run(self, option, value=None):
        if option == "modules":
            h = Module.get_help(value)
            if h.strip() != "":
                print_formatted_text(h)
            else:
                self.logger.warning("No module loaded")
        elif option == "options":
            data = [["Name", "Value", "Required", "Description"]]
            for n, d, v, r in sorted(self.config.items(), key=lambda x: x[0]):
                if value is None or n == value:
                    data.append([n, v, ["N", "Y"][r], d])
            print_formatted_text(BorderlessTable(data, "Console options"))
        elif option == "projects":
            if value is None:
                data = [["Name"]]
                for p in projects(self):
                    data.append([p])
                print_formatted_text(BorderlessTable(data, "Existing projects"))
            else:
                print_formatted_text(value)


# ---------------------------- OPTIONS-RELATED COMMANDS ------------------------
class Set(Command):
    """ Set an option in the current context """
    def complete_values(self, option):
        if option.upper() == "WORKSPACE":
            return [str(x) for x in Path(".").home().iterpubdir()]
    
    def run(self, option, value):
        self.config[option] = value
        print_formatted_text("{} => {}".format(option,
                             self.config.option(option).value))
    
    def validate(self, option, value):
        assert option in self.config.keys(), "Invalid option"
        r = self.config.option(option).required
        assert not r or (r and value is not None), "A value is required"


class Unset(Command):
    """ Unset an option from the current context """
    def run(self, option):
        self.config[option] = None
        self.logger.debug("Unset {}".format(option))
    
    def validate(self, option, value):
        r = self.config.option(option).required
        assert not r or (r and value is not None), "A value is required"

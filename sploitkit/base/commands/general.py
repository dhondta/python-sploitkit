from __future__ import unicode_literals, print_function

import shlex
from sploitkit import *
from subprocess import call


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
    def run(self, text):
        keywords = shlex.split(text)
        i = 0
        for m in Module._subclasses:
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
    """ Show console options """
    values = ["options"]
    
    def run(self, value):
        if value == "options":
            data = [["Name", "Value", "Description"]]
            for k, d, v in sorted(self.config.items(), key=lambda x: x[0]):
                data.append([k, v, d])
            print_formatted_text(BorderlessTable(data, "Console options"))


# ---------------------------- OPTIONS-RELATED COMMANDS ------------------------
class Set(Command):
    """ Set an option in the current context """
    def complete_values(self, option):
        if option.upper() == "WORKSPACE":
            return [str(x) for x in Path(".").home().iterpubdir()]
    
    def run(self, option, value):
        if value.lower() in ["true", "false"]:
            value = value == "true"
        elif value.isdigit():
            value = int(value)
        self.config[option] = value
        self.logger.debug("Set {} to {}".format(option, value))
    
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

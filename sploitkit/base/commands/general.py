# -*- coding: UTF-8 -*-
import re
import shlex

from sploitkit import *

projects = lambda cmd: [x.filename for x in cmd.workspace.iterpubdir()]


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
    single_arg = True

    def run(self, text):
        keywords = shlex.split(text)
        data = [["Name", "Path", "Description"]]
        for m in Module.subclasses:
            for k in keywords:
                if m.search(k):
                    data.append([m.name, m.path, m.description])
        if len(data) == 1:
            self.logger.error("No match found")
        else:
            t = BorderlessTable(data, "Matching modules")
            print_formatted_text(t.table)
            n = len(data) - 1
            self.logger.info("{} match{} found".format(n, ["", "es"][n > 0]))


class Show(Command):
    """ Show options, projects, modules or issues (if any) """
    level = "root"
    keys = ["modules", "options", "projects"]

    def __init__(self):
        if Entity.has_issues():
            self.keys = self.keys + ["issues"]

    def complete_values(self, key):
        if key == "modules":
            return [m for m in self.console.modules.keys()]
        elif key == "options":
            return self.config.keys()
        elif key == "projects":
            return projects(self)
        elif key == "issues":
            l = []
            for cls, subcls, errors in Entity.get_issues():
                l.extend(errors.keys())
            return l

    def run(self, key, value=None):
        if key == "modules":
            h = Module.get_help(value)
            if h.strip() != "":
                print_formatted_text(h)
            else:
                self.logger.warning("No module loaded")
        elif key == "options":
            data = [["Name", "Value", "Required", "Description"]]
            for n, d, v, r in sorted(self.config.items(), key=lambda x: x[0]):
                if value is None or n == value:
                    data.append([n, v, ["N", "Y"][r], d])
            print_formatted_text(BorderlessTable(data, "Console options"))
        elif key == "projects":
            if value is None:
                data = [["Name"]]
                for p in projects(self):
                    data.append([p])
                print_formatted_text(BorderlessTable(data, "Existing projects"))
            else:
                print_formatted_text(value)
        elif key == "issues":
            # message formatting function
            def msg(key, item):
                if key == "file":
                    return "'{}' not found".format(item)
                elif key == "packages":
                    return "'{}' system package is not installed".format(item)
                elif key == "python":
                    return "'{}' Python package is not installed".format(item)
                elif key == "tools":
                    return "'{}' tool is not installed".format(item)
                elif key == "state":
                    item = re.split(r"(\=|\?)", item, 1)
                    if len(item) == 1:
                        return "'{}' state key is not defined".format(item[0])
                    elif item[1] == "=":
                        return "'{}' state key does not match the expected " \
                               "value '{}'".format(item[0], item[2])
                    elif item[1] == "?":
                        return "'{}' state key is expected to have value '{}'" \
                               " at least once".format(item[0], item[2])

            if Entity.has_issues():
                print("")
            for cls, subcls, errors in Entity.get_issues():
                if value is None:
                    t = "{}: {}\n- ".format(cls, subcls)
                    t += "\n- ".join(msg(k, e) for k, err in errors.items() \
                                     for e in err) + "\n"
                else:
                    t = ""
                    for k, e in errors.items():
                        if k == value:
                            t += "- {}/{}: {}".format(cls, subcls, e)
                print_formatted_text(t)


# ---------------------------- OPTIONS-RELATED COMMANDS ------------------------
class Set(Command):
    """ Set an option in the current context """

    def complete_keys(self):
        return list(self.config.keys())

    def complete_values(self, key):
        if key.upper() == "WORKSPACE":
            return [str(x) for x in Path(".").home().iterpubdir()]
        return self.config.option(key).choices or []

    def run(self, key, value):
        self.config[key] = value
        self.logger.success("{} => {}"
                            .format(key, self.config.option(key).value))
        if hasattr(self.config, "_last_error"):
            self.logger.warning("Callback error: {}"
                                .format(self.config._last_error))

    def validate(self, key, value):
        if key not in self.config.keys():
            raise ValueError("invalid key")
        o = self.config.option(key)
        if o.required and value is None:
            raise ValueError("a value is required")
        if not o.validate(value):
            raise ValueError("invalid value")


class Unset(Command):
    """ Unset an option from the current context """

    def complete_keys(self):
        return list(self.console.config.keys())

    def run(self, key):
        self.config[key] = None
        self.logger.debug("{} => null".format(key))

    def validate(self, key):
        if key not in self.config.keys():
            raise ValueError("invalid key")
        r = self.config.option(key).required
        if r and value is None:
            raise ValueError("a value is required")

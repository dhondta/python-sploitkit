# -*- coding: UTF-8 -*-
import re
import shlex
from prompt_toolkit.formatted_text import ANSI
from tinyscript.helpers import human_readable_size, BorderlessTable, Path

from sploitkit import *
from sploitkit.core.module import MetaModule


projects = lambda cmd: [x.filename for x in cmd.workspace.iterpubdir()]


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Back(Command):
    """ Come back to the previous console level """
    except_levels = ["root", "session"]
    
    def run(self):
        raise ConsoleExit


class Exit(Command):
    """ Exit the console """
    aliases = ["quit"]
    except_levels = ["session"]
       
    def run(self):
        raise ConsoleExit


class Help(Command):
    """ Display help """
    aliases = ["?"]
    
    def run(self):
        print_formatted_text(Command.get_help("general", self.console.level))


class Search(Command):
    """ Search for text in modules """
    except_levels = ["session"]
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
            n = len(data) - 2
            self.logger.info(f"{n} match{['', 'es'][n > 0]} found")


class Show(Command):
    """ Show options, projects, modules or issues (if any) """
    level = "root"
    keys = ["files", "modules", "options", "projects"]
    
    def complete_values(self, key):
        if key == "files":
            if self.config.option("TEXT_VIEWER").value is not None:
                return list(map(str, self.console._files.list))
            return []
        elif key == "issues":
            l = []
            for cls, subcls, errors in Entity.issues():
                l.extend(list(errors.keys()))
            return l
        elif key == "modules":
            uncat = any(isinstance(m, MetaModule) for m in self.console.modules.values())
            l = [c for c, m in self.console.modules.items() if not isinstance(m, MetaModule)]
            return l + ["uncategorized"] if uncat else l
        elif key == "options":
            return list(self.config.keys())
        elif key == "projects":
            return projects(self)
        elif key == "sessions":
            return [str(i) for i, _ in self.console._sessions]
    
    def run(self, key, value=None):
        if key == "files":
            if value is None:
                data = [["Path", "Size"]]
                p = Path(self.config.option("WORKSPACE").value)
                for f in self.console._files.list:
                    data.append([f, human_readable_size(p.joinpath(f).size)])
                print_formatted_text(BorderlessTable(data, "Files from the workspace"))
            elif self.config.option("TEXT_VIEWER").value:
                self.console._files.view(value)
        elif key == "issues":
            t = Entity.get_issues()
            if len(t) > 0:
                print_formatted_text(t)
        elif key == "modules":
            h = Module.get_help(value)
            if h.strip() != "":
                print_formatted_text(h)
            else:
                self.logger.warning("No module loaded")
        elif key == "options":
            if value is None:
                print_formatted_text(ANSI(str(self.config)))
            else:
                c = Config()
                c[self.config.option(value)] = self.config[value]
                print_formatted_text(ANSI(str(c)))
        elif key == "projects":
            if value is None:
                data = [["Name"]]
                for p in projects(self):
                    data.append([p])
                print_formatted_text(BorderlessTable(data, "Existing projects"))
            else:
                print_formatted_text(value)
        elif key == "sessions":
            data = [["ID", "Description"]]
            for i, s in self.console._sessions:
                data.append([str(i), getattr(s, "description", "<undefined>")])
                print_formatted_text(BorderlessTable(data, "Open sessions"))
    
    def set_keys(self):
        if Entity.has_issues():
            self.keys += ["issues"]
        else:
            while "issues" in self.keys:
                self.keys.remove("issues")
        if len(self.console._sessions) > 0:
            self.keys += ["sessions"]
        else:
            while "sessions" in self.keys:
                self.keys.remove("sessions")
    
    def validate(self, key, value=None):
        if key not in self.keys:
            raise ValueError("invalid key")
        if value is not None:
            if key == "files":
                if self.config.option("TEXT_VIEWER").value is None:
                    raise ValueError("cannot view file ; TEXT_VIEWER is not set")
                if value not in self.complete_values(key):
                    raise ValueError("invalid file")
            elif key == "issues":
                if value not in self.complete_values(key):
                    raise ValueError("invalid error type")
            elif key == "modules":
                if value is not None and value not in self.complete_values(key):
                    raise ValueError("invalid module")
            elif key == "options":
                if value is not None and value not in self.complete_values(key):
                    raise ValueError("invalid option")
            elif key == "projects":
                if value is not None and value not in self.complete_values(key):
                    raise ValueError("invalid project name")


# ---------------------------- OPTIONS-RELATED COMMANDS ------------------------
class Set(Command):
    """ Set an option in the current context """
    except_levels = ["session"]
    
    def complete_keys(self):
        return self.config.keys()
    
    def complete_values(self, key):
        if key.upper() == "WORKSPACE":
            return [str(x) for x in Path(".").home().iterpubdir()]
        return self.config.option(key).choices or []
    
    def run(self, key, value):
        self.config[key] = value
    
    def validate(self, key, value):
        if key not in self.config.keys():
            raise ValueError("invalid option")
        o = self.config.option(key)
        if o.required and value is None:
            raise ValueError("a value is required")
        if not o.validate(value):
            raise ValueError("invalid value")


class Unset(Command):
    """ Unset an option from the current context """
    except_levels = ["session"]
    
    def complete_values(self):
        for k in self.config.keys():
            if not self.config.option(k).required:
                yield k
    
    def run(self, key):
        del self.config[key]
    
    def validate(self, key):
        if key not in self.config.keys():
            raise ValueError("invalid option")
        if self.config.option(key).required:
            raise ValueError("this option is required")


class Setg(Command):
    """ Set a global option """
    except_levels = ["session"]
    
    def complete_keys(self):
        return self.config.keys(True)
    
    def complete_values(self, key):
        return self.config.option(key).choices or []
    
    def run(self, key, value):
        self.config.setglobal(key, value)
    
    def validate(self, key, value):
        try:
            o = self.config.option(key)
            if not o.glob:
                raise ValueError("cannot be set as global")
            if not o.validate(value):
                raise ValueError("invalid value")
        except KeyError:
            pass


class Unsetg(Command):
    """ Unset a global option """
    except_levels = ["session"]
    
    def complete_values(self):
        return self.config._g.keys()
    
    def run(self, key):
        self.config.unsetglobal(key)
    
    def validate(self, key):
        if key not in self.config._g.keys():
            raise ValueError("invalid option")


# -*- coding: UTF-8 -*-
import os
import stat
import yaml
from collections.abc import Iterable
from gc import collect, get_objects, get_referrers
from subprocess import call
from sys import getrefcount
from tinyscript.helpers import human_readable_size, parse_docstring, pprint, BorderlessTable, Capture, Path

from sploitkit import *
from sploitkit.core.components import BACK_REFERENCES
from sploitkit.core.entity import load_entities


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Edit(Command):
    """ Edit a text file """
    except_levels = ["session"]
    requirements = {'system': ["vim"]}
    single_arg   = True
    
    def check_requirements(self):
        return self.config.option("TEXT_EDITOR").value is not None
    
    def complete_values(self):
        p = Path(self.config.option("WORKSPACE").value)
        f = p.iterfiles(relative=True)
        return list(map(lambda x: str(x), f))
    
    def run(self, filename):
        f = Path(self.config.option("WORKSPACE").value).joinpath(filename)
        self.console._files.edit(str(f))
    
    def validate(self, filename):
        return


class History(Command):
    """ Inspect commands history """
    except_levels = ["session"]
    requirements = {'system': ["less"]}
    
    def run(self):
        h = Path(self.config.option("WORKSPACE").value).joinpath("history")
        self.console._files.page(str(h))


class Shell(Command):
    """ Execute a shell command """
    except_levels = ["session"]
    single_arg = True
    
    def complete_values(self):
        l = []
        e = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
        for p in os.environ['PATH'].split(":"):
            if not os.path.isdir(p):
                continue
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.isfile(fp):
                    st = os.stat(fp)
                    if st.st_mode & e and f not in l:
                        l.append(f)
        return l
        
    def run(self, cmd=None):
        if cmd is None:
            from pty import spawn
            spawn("/bin/bash")
        else:
            call(cmd, shell=True)
        print_formatted_text("")
    
    def validate(self, cmd):
        _ = cmd.split()
        if len(_) <= 1 and _[0] not in self.complete_values():
            raise ValueError("bad shell command")


class Stats(Command):
    """ Display console's statistics """
    level = "root"
    
    def run(self):
        d = [["Item", "Path", "Size"]]
        p = self.console.app_folder
        d.append(["APP_FOLDER", str(p), human_readable_size(p.size)])
        p = self.workspace
        d.append(["WORKSPACE", str(p), human_readable_size(p.size)])
        t = BorderlessTable(d, "Statistics")
        print_formatted_text(t.table)


# ------------------------------- DEBUGGING COMMANDS ---------------------------
class DebugCommand(Command):
    """ Proxy class for development commands """
    except_levels = ["session"]
    requirements = {'config': {'DEBUG': True}}


class Logs(DebugCommand):
    """ Inspect console logs """
    requirements = {'system': ["less"]}
    
    def run(self):
        self.console._files.page(self.logger.__logfile__)


class Pydbg(DebugCommand):
    """ Start a Python debugger session """
    requirements = {'python': ["pdb"]}

    def run(self):
        import pdb
        pdb.set_trace()


class State(DebugCommand):
    """ Display console's shared state """
    def run(self):
        for k, v in self.console.state.items():
            print_formatted_text(f"\n{k}:")
            v = v or ""
            if len(v) == 0:
                continue
            if isinstance(v, Iterable):
                if isinstance(v, dict):
                    v = dict(**v)
                for l in yaml.dump(v).split("\n"):
                    if len(l.strip()) == 0:
                        continue
                    print_formatted_text("  " + l)
            else:
                print_formatted_text(v)
        print_formatted_text("")


# ------------------------------ DEVELOPMENT COMMANDS --------------------------
class DevCommand(DebugCommand):
    """ Proxy class for development commands """
    def condition(self):
        return getattr(Console, "_dev_mode", False)


class Collect(DevCommand):
    """ Garbage-collect """
    def run(self):
        collect()


class Dict(DevCommand):
    """ Show console's dictionary of attributes """
    def run(self):
        pprint(self.console.__dict__)


class Memory(DevCommand):
    """ Inspect memory consumption """
    keys         = ["graph", "growth", "info", "leaking", "objects", "refs"]
    requirements = {
        'python': ["objgraph", "psutil", "xdot"],
        'system': ["xdot"],
    }
    
    def complete_values(self, key=None):
        if key in ["graph", "refs"]:
            return [str(o) for o in get_objects() if isinstance(o, Console)]
    
    def run(self, key, value=None):
        if value is not None:
            obj = list(filter(lambda o: str(o) == value, get_objects()))[0]
        if key == "graph":
            from objgraph import show_refs
            if value is None:
                p = self.console.parent
                show_refs(self.console if p is None else p, refcounts=True, max_depth=3)
            else:
                show_refs(obj, refcounts=True, max_depth=3)
        elif key == "growth":
            from objgraph import get_leaking_objects, show_most_common_types
            show_most_common_types(objects=get_leaking_objects())
        elif key == "info":
            from psutil import Process
            p = Process(os.getpid())
            print_formatted_text(p.memory_info())
        elif key == "leaking":
            from objgraph import get_leaking_objects
            with Capture() as (out, err):
                pprint(get_leaking_objects())
            print_formatted_text(out)
        elif key == "objects":
            data = [["Object", "#References"]]
            for o in get_objects():
                if isinstance(o, (Console, Module)):
                    data.append([str(o), str(getrefcount(o))])
            t = BorderlessTable(data, "Consoles/Modules")
            print_formatted_text(t.table)
        elif key == "refs":
            if value is not None:
                print_formatted_text(getrefcount(obj), ":")
                pprint(get_referrers(obj))
    
    def validate(self, key, value=None):
        if key in ["graph", "refs"]:
            if value and value not in self.complete_values("graph"):
                raise ValueError("bad object")
        elif value:
            raise ValueError("this key takes no value")


class Reload(Command):
    """ Inspect memory consumption """
    level  = "root"
    values = ["commands", "modules", "models"]
    
    def condition(self):
        return getattr(Console, "_dev_mode", False)
    
    def run(self, value):
        load_entities([globals()[value[:-1].capitalize()]],
                      *([self.console._root] + self.console._sources("entities")), **self.console._load_kwargs)


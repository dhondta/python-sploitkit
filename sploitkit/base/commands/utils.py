# -*- coding: UTF-8 -*-
import os
import stat
import yaml
from collections.abc import Iterable
from gc import collect, get_objects, get_referrers
from pprint import pprint
from subprocess import call
from sys import getrefcount

from sploitkit import *


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Edit(Command):
    """ Edit a file with PyVim """
    requirements = {'python': ["pyvim"]}
    single_arg   = True
    
    def complete_values(self):
        p = self.config.option("WORKSPACE").value
        f = Path(p).iterfiles(relative=True)
        return list(map(lambda _: str(_), f))
    
    def run(self, filename):
        f = Path(self.config.option("WORKSPACE").value).joinpath(filename)
        edit_file(str(f))


class History(Command):
    """ Inspect commands history """
    requirements = {'python': ["pypager"]}
    
    def run(self):
        h = Path(self.config.option("WORKSPACE").value).joinpath("history")
        page_file(str(h))


class Shell(Command):
    """ Execute a shell command """
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
        _ = self.console.app_folder
        d.append(["APP_FOLDER", str(_), human_readable_size(_.size)])
        _ = self.workspace
        d.append(["WORKSPACE", str(_), human_readable_size(_.size)])
        t = BorderlessTable(d, "Statistics")
        print_formatted_text(t.table)


# ------------------------------- DEBUGGING COMMANDS ---------------------------
class Logs(Command):
    """ Inspect console logs """
    requirements = {
        'config': {'DEBUG': True},
        'python': ["pypager"],
    }
    
    def run(self):
        page_file(self.logger.__logfile__)


class Pydbg(Command):
    """ Start a Python debugger session """
    requirements = {
        'config': {'DEBUG': True},
        'python': ["pdb"],
    }

    def run(self):
        import pdb
        pdb.set_trace()


class State(Command):
    """ Display console's shared state """
    requirements = {'config': {'DEBUG': True}}

    def run(self):
        for k, v in self.console.state.items():
            print_formatted_text("\n{}:".format(k))
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
class DevCommand(Command):
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
                show_refs(self.console if self.console.parent is None else \
                          self.console.parent, refcounts=True, max_depth=3)
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
            print_formatted_text(get_leaking_objects())
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

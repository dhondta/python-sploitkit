# -*- coding: UTF-8 -*-
import os
import stat
from gc import get_objects, get_referrers
from sys import getrefcount

from sploitkit import *


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Memory(Command):
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
            print(p.memory_info())
        elif key == "leaking":
            from objgraph import get_leaking_objects
            print(get_leaking_objects())
        elif key == "objects":
            for o in get_objects():
                if isinstance(o, (Console, Module)):
                    print(o)
        elif key == "refs":
            if value is not None:
                print(getrefcount(obj), ":", get_referrers(obj))
    
    def validate(self, key, value=None):
        if key in ["graph", "refs"]:
            if value and value not in self.complete_values("graph"):
                raise ValueError("bad object")
        elif value:
            raise ValueError("this key takes no value")


class Pydbg(Command):
    """ Start a Python debugger session """
    requirements = {'python': ["pdb"]}

    def run(self):
        import pdb
        pdb.set_trace()


class Shell(Command):
    """ Execute a shell command """
    splitargs = False
    
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
        from subprocess import call
        call("/bin/bash" if cmd is None else cmd, shell=True)
        print("")

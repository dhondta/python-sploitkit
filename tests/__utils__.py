 #!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Test utility functions.

"""
import os
import pytest
import re
import sys
from peewee import DoesNotExist
from subprocess import Popen, PIPE
from tinyscript.helpers import ClassRegistry, Path
from unittest import TestCase
from unittest.mock import patch

from sploitkit import *
from sploitkit.__info__ import *
from sploitkit.core.entity import load_entities, Entity

from testsploit.main import MySploitConsole


__all__ = ["CONSOLE", "execute", "patch", "rcfile", "reset_entities", "BaseModel", "Command", "Console", "DoesNotExist",
           "Entity", "Model", "Module", "StoreExtension", "TestCase"]


try:
    CONSOLE = MySploitConsole()
    CONSOLE.config['APP_FOLDER'] = "testsploit/workspace"
    CONSOLE.config['WORKSPACE'] = "testsploit/workspace"
except:
    CONSOLE = MySploitConsole.parent
FILE = ".commands.rc"


def execute(*commands):
    """ Execute commands. """
    c = list(commands) + ["exit"]
    p = os.path.join("testsploit", FILE)
    with open(p, 'w') as f:
        f.write("\n".join(c))
    r = rcfile(FILE)
    os.remove(p)
    return r


def rcfile(rcfile, debug=False):
    """ Execute commands using a rcfile. """
    p = os.path.join("testsploit", rcfile)
    if not os.path.isfile(p):
        raise ValueError("Bad rc file")
    cmd = "cd testsploit && python3 main.py --rcfile %s" % rcfile
    if debug:
        cmd += " -v"
    out, err = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True).communicate()
    out = re.split(r"\+{10,}\s.*?\s\+{10,}", out.decode())[1:]
    err = "\n".join(l for l in err.decode().splitlines() if not l.startswith("Warning: ") and \
          all(x not in l for x in ["DeprecationWarning: ", "import pkg_resources", "There are some issues"])).strip()
    c = []
    with open(p) as f:
        for l in f:
            l = l.strip()
            try:
                c.append((l, re.sub(r"\x1b\[\??\d{1,3}[hm]", "", out.pop(0)).strip()))
            except IndexError:
                c.append((l, None))
    if c[-1][0] == "exit":
        c.pop(-1)
    return c, err


def reset_entities(*entities):
    entities = list(entities) or [BaseModel, Command, Console, Model, Module, StoreExtension]
    Entity._subclasses = ClassRegistry()
    load_entities(entities)


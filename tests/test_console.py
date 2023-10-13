#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Core entity assets' tests.

"""
from sploitkit.core.components import *

from __utils__ import *


class TestConsole(TestCase):
    def test_console(self):
        self.assertIsNotNone(CONSOLE._get_tokens("help"))
        self.assertIsNone(CONSOLE.play("help"))
        r = CONSOLE.play("help", "show modules", capture=True)
        # check the presence of some commands from the base
        for cmd in ["?", "exit", "quit", "unset", "use", "record", "replay", "help", "show", "select"]:
            self.assertIn(" " + cmd + " ", r[0][1])
        # check that some particular commands are missing
        for cmd in ["pydbg", "memory", "dict"]:
            self.assertNotIn(" " + cmd + " ", r[0][1])


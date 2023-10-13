#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Core entity assets' tests.

"""
from __utils__ import *


class TestBase(TestCase):
    def test_general_commands(self):
        self.assertRaises(SystemExit, Entity.get_subclass(Command, "Back")().run)
        self.assertRaises(SystemExit, Entity.get_subclass(Command, "Exit")().run)
        for Help in Entity.get_subclass(Command, "Help"):
            if Help.level == "general":
                self.assertIsNone(Help().run())
        search = Entity.get_subclass(Command, "Search")()
        self.assertIsNone(search.run("does_not_exist"))
        self.assertIsNone(search.run("first"))
        for Show in Entity.get_subclass(Command, "Show"):
            if Show.level == "root":
                Show.keys += ["issues"]
                Show().set_keys()
                for k in Show.keys + ["issues"]:
                    self.assertIsNotNone(Show().complete_values(k))
                    self.assertIsNone(Show().run(k))
                    if k == "options":
                        self.assertIsNone(Show().run(k, "DEBUG"))
                break
        Set = Entity.get_subclass(Command, "Set")
        keys = list(Set().complete_keys())
        self.assertTrue(len(keys) > 0)
        self.assertIsNotNone(Set().complete_values(keys[0]))
        self.assertIsNotNone(Set().complete_values("WORKSPACE"))
        self.assertRaises(ValueError, Set().validate, "BAD", "whatever")
        self.assertRaises(ValueError, Set().validate, "WORKSPACE", None)
        self.assertRaises(ValueError, Set().validate, "DEBUG", "whatever")
        self.assertIsNone(Set().run("DEBUG", "false"))
        Unset = Entity.get_subclass(Command, "Unset")
        self.assertTrue(len(list(Unset().complete_values())) > 0)
        self.assertRaises(ValueError, Unset().validate, "BAD")
        self.assertRaises(ValueError, Unset().validate, "WORKSPACE")
        self.assertRaises(ValueError, Unset().run, "DEBUG")
        self.assertIsNone(Set().run("DEBUG", "false"))
    
    def test_root_commands(self):
        for Help in Entity.get_subclass(Command, "Help"):
            if Help.level == "root":
                self.assertIsNone(Help().validate())
                self.assertRaises(ValueError, Help().validate, "BAD")
                self.assertIsNone(Help().run())
                for k in Help().keys:
                    for v in Help().complete_values(k):
                        self.assertIsNone(Help().run(k, v))
                break


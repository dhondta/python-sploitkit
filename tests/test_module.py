#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module entity tests.

"""
from __utils__ import *


class TestModule(TestCase):
    def test_module_attributes(self):
        for m in Module.subclasses:
            m.console = CONSOLE  # use the main console ; should normally be a ModuleConsole
            self.assertIsNotNone(m.base)
            for a in ["files", "logger", "store", "workspace"]:
                self.assertIsNotNone(getattr(m(), a))
    
    def test_module_help(self):
        for c in [None, "uncategorized", "does_not_exist"]:
            self.assertIsNotNone(Module.get_help(c))
        M = Module.subclasses[0]
        self.assertIsNone(M()._feedback(None, ""))
        self.assertIsNone(M()._feedback(True, "test"))
        self.assertIsNone(M()._feedback(False, "test"))
    
    def test_module_registry(self):
        self.assertIsNotNone(Module.get_list())
        self.assertIsNotNone(Module.get_modules())
        class FakeModule(Module):
            path = "fake_module"
            name = "fake_module"
        self.assertIsNone(Module.unregister_module(FakeModule))
        class OrphanModule(Module):
            path = None
            name = "orphan_module"
        self.assertIsNone(Module.register_module(OrphanModule))
        self.assertNotIn(OrphanModule, Module.subclasses)


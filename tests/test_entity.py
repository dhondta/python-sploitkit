#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Core entity assets' tests.

"""
from sploitkit.core.entity import load_entities, set_metadata
from tinyscript.helpers import parse_docstring

from __utils__ import *


class TestEntity(TestCase):
    def test_load_entities(self):
        self.assertIn(Command, list(Entity._subclasses.keys()))
        self.assertIn(Model, list(Entity._subclasses.keys()))
        self.assertIn(Module, list(Entity._subclasses.keys()))
        self.assertTrue(len(Command.subclasses) > 0)
        self.assertTrue(len(Model.subclasses) > 0)
        l = len(Module.subclasses)
        self.assertTrue(l > 0)
        M = Module.subclasses[0]
        del Entity._subclasses[Module]
        load_entities([Module], CONSOLE._root.dirname.joinpath("modules"), exclude={'module': [M]})
        self.assertTrue(len(Module.subclasses) > 0)
        self.assertRaises(ValueError, Entity._subclasses.__getitem__, (Module, M.__name__))
        del Entity._subclasses[Module]
        load_entities([Module], CONSOLE._root.dirname.joinpath("modules"))
        self.assertTrue(len(Module.subclasses) > 0)
        self.assertIn(Entity._subclasses[Module, M.__name__], Module.subclasses)
        load_entities([Console], CONSOLE._root, backref={'command': ["console"]})
    
    def test_set_metadata(self):
        # check that every subclass has its own description, and not the one of its entity class
        for cls in Entity._subclasses.keys():
            for subcls in cls.subclasses:
                self.assertNotEqual(subcls.__doc__, cls.__doc__)
        # now, alter a Command subclass to test for set_metadata
        C = Command.subclasses[0]
        C.meta = {'options': ["BAD_OPTION"]}
        self.assertRaises(ValueError, set_metadata, C, parse_docstring)
        C.meta = {'options': [("test", "default", False, "description")]}
        set_metadata(C, parse_docstring)
        M = Module.subclasses[0]
        B = M.__base__
        B.meta = {'test': "test"}
        M._inherit_metadata = True
        set_metadata(M, parse_docstring)


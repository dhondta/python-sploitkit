#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Model entity tests.

"""
from __utils__ import *


class TestModule(TestCase):
    def test_model(self):
        self.assertTrue(len(Model.subclasses) > 0)
        self.assertTrue(len(StoreExtension.subclasses) == 0)  # sploitkit's base has no StoreExtension at this moment
        self.assertIsNotNone(repr(Model.subclasses[0]))


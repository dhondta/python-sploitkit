#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Core entity assets' tests.

"""
from sploitkit.core.components import *

from __utils__ import *


class TestComponents(TestCase):
    def test_store(self):
        s = CONSOLE._storage
        self.assertTrue(isinstance(s.extensions, list))
        s = CONSOLE.store
        self.assertTrue(isinstance(s.basemodels, list))
        self.assertTrue(isinstance(s.models, list))
        self.assertFalse(s.volatile)
        try:
            s.get_user(username="test")
        except DoesNotExist:
            s.set_user(username="test")
        self.assertEqual(s._last_snapshot, 0)
        self.assertIsNone(s.snapshot())
        self.assertEqual(s._last_snapshot, 1)
        self.assertIsNone(s.snapshot(False))
        self.assertEqual(s._last_snapshot, 0)
        self.assertIsNone(s.snapshot(False))


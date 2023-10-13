#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Scenario-based tests of a Sploitkit application.

"""
from __utils__ import *


class TestScenarios(TestCase):
    def test_bad_command(self):
        # single bad command
        out, err = execute("bad")
        self.assertNotEqual(err, "")
        self.assertEqual(out[0][1], "")
        # successful command before the failing one
        out, err = execute("help", "bad")
        self.assertNotEqual(err, "")
        self.assertNotEqual(out[0][1], "")
        self.assertEqual(out[1][1], "")
        # failing command before the successful one
        out, err = execute("bad", "help")
        self.assertNotEqual(err, "")
        self.assertEqual(out[0][1], "")
        self.assertIsNone(out[1][1])
    
    def test_help(self):
        out, err = execute("help")
        self.assertEqual(err, "")
        self.assertNotEqual(out, "")
        out, err = execute("?")
        self.assertEqual(err, "")
        self.assertNotEqual(out, "")
    
    def test_set_debug(self):
        out, err = execute("set DEBUG true", "help")
    
    def test_show_modules(self):
        out, err = execute("show modules")
        self.assertEqual(err, "")
        self.assertIn("modules", out[0][1])
        self.assertIn("my_first_module", out[0][1])
    
    def test_show_options(self):
        out, err = execute("show options")
        self.assertEqual(err, "")
        self.assertIn("Console options", out[0][1])
        self.assertIn("APP_FOLDER", out[0][1])
        self.assertIn("DEBUG", out[0][1])
        self.assertIn("WORKSPACE", out[0][1])
    
    def test_show_projects(self):
        out, err = execute("show projects")
        self.assertEqual(err, "")
        self.assertIn("Existing projects", out[0][1])


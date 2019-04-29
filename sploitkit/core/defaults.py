from __future__ import unicode_literals


__all__ = ["COMMAND_SOURCES", "MODULE_SOURCES", "ROOT_LEVEL"]


ROOT_LEVEL = "root"  # console root level's name

# list of Python module names from which the console commands are to be loaded
COMMAND_SOURCES = ["commands"]

# list of Python module names from which the console modules are to be loaded
MODULE_SOURCES  = ["modules"]

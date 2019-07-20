from __future__ import unicode_literals

import gc
import re
from inspect import getargspec

from .entity import Entity, MetaEntity
from ..utils.misc import failsafe
from ..utils.objects import BorderlessTable, NameDescription
from ..utils.path import Path, PyModulePath


__all__ = ["Command"]


COMMAND_STYLES = [
    "lowercase",   # ClassName => classname
    "none",        # ClassName => ClassName
    "powershell",  # ClassName => Class-Name
    "slugified",   # ClassName => class-name
    "uppercase"    # ClassName => CLASSNAME
]
"""
Usage:
  >>> from sploitkit import Command
  >>> Command.set_style("powershell")
"""
FUNCTIONALITIES = [
    "general",    # commands for every level
    "utils",      # utility commands (for every level)
    "recording",  # recording commands (for every level)
    "root",       # base root-level commands
    "project",    # base project-level commands
    "module",     # base module-level commands
]


class MetaCommand(MetaEntity):
    """ Metaclass of a Command. """
    style = "slugified"
    
    def __init__(self, *args):
        argspec = getargspec(self.run)
        s, args, defs = "{}", argspec.args[1:], argspec.defaults
        for a in args[:len(args)-len(defs or [])]:
            s += " " + a
        if len(defs or []) > 0:
            s += " ["
            i = []
            for a, d in zip(args[len(args)-len(defs):], defs):
                i.append("{}={}".format(a, d) if d is not None else a)
            s += " ".join(i) + "]"
        self.signature = s
        self.args, self.defaults = args, defs
    
    def help(self, alias=None):
        """ Help message for the command, formatted as a row with its name and 
             description, with the alias instead of the name if defined. """
        name = alias or self.name
        return NameDescription(name, self.description, self.details)
    
    @property
    def name(self):
        """ Command name, according to the defined style. """
        _ = self.__name__
        if self.style == "lowercase":
            _ = _.lower()
        elif self.style in ["powershell", "slugified"]:
            _ = re.sub(r'(.)([A-Z][a-z]+)', r'\1-\2', _)
            _ = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', _)
            _ = _.lower() if self.style == "slugified" else _
        elif self.style == "uppercase":
            _ = _.upper()
        return _


class Command(Entity, metaclass=MetaCommand):
    """ Main class handling console commands. """
    aliases       = []
    alias_only    = False
    commands      = {}
    level         = "general"
    levels        = []
    except_levels = []
    splitargs     = True
    
    @property
    def _nargs(self):
        """ Get run's signature info (n = number of args,
                                      m = number of args with no default). """
        argspec = getargspec(self.run)
        n = len(argspec.args) - 1  # substract 1 for self
        return n, n - len(argspec.defaults or ())
    
    @property
    @failsafe
    def config(self):
        """ Command console-bound config (shorcut). """
        return self.console.config
    
    @property
    @failsafe
    def logger(self):
        """ Command console-bound logger (shorcut). """
        return self.console.logger
    
    @property
    @failsafe
    def options(self):
        """ Command console-bound options (shorcut). """
        return self.console.config.keys()

    @classmethod
    def get_help(cls, *levels):
        """ Display commands' help(s), using its metaclass' properties. """
        if len(levels) == 2 and "general" in levels:
            # process a new dictionary of commands, handling levels in order (so
            #  that it resolves command name conflicts between levels by itself)
            _ = {}
            for l in levels:
                for n, c in cls.commands.get(l, {}).items():
                    if c.level != "general" or all(l not in levels for l in \
                                                   c.except_levels):
                        _[n] = c
            # then rebuild the dictionary by levels from this dictionary
            levels = {"general": {}, "specific": {}}
            for n, c in _.items():
                levels[["specific", "general"][c.level == "general"]][n] = c
        else:
            _, levels = levels, {}
            for l in _:
                levels[l] = cls.commands[l]
        # now make the help with tables of command name-descriptions by level
        s, i = "", 0
        for l, cmds in sorted(levels.items(), key=lambda x: x[0]):
            if len(cmds) == 0:
                continue
            d = [["Name", "Description"]]
            for n, c in sorted(cmds.items(), key=lambda x: x[0]):
                d.append([n, c.description])
            t = BorderlessTable(d, "{} commands".format(l.capitalize()))
            s += t.table + "\n\n"
            i += 1
        return "\n" + s.strip() + "\n" if i > 0 else ""

    @classmethod
    def register_command(cls, subcls):
        """ Register the command and its aliases in a dictionary according to
             its level. """
        l = subcls.level
        cls.commands.setdefault(l, {})
        if l not in cls.levels:
            cls.levels.append(l)
        if not subcls.alias_only:
            cls.commands[l][subcls.name] = subcls
        for alias in subcls.aliases:
            cls.commands[l][alias] = subcls
    
    @classmethod
    def set_style(cls, style):
        """ Set the style of command name. """
        assert style in COMMAND_STYLES, "Command style must be one of the " \
               "followings: [{}]".format("|".join(COMMAND_STYLES))
        MetaCommand.style = style
    
    @classmethod
    def unregister_command(cls, subcls):
        """ Unregister a command class from the subclasses and the commands
             dictionary. """
        l, n = subcls.level, subcls.name
        # remove every reference in commands dictionary
        for n in [n] + subcls.aliases:
            try:
                del Command.commands[l][n]
            except KeyError:
                pass
        # remove the subclass instance from the subclasses registry
        try:
            Command.subclasses.remove(subcls)
        except ValueError:
            pass
        # remove the subclass from the global namespace (if not Command itself)
        if subcls is not Command:
            try:
                del globals()[subcls.__name__]
            except KeyError:
                pass
        # if the level of commands is become empty, remove it
        if len(Command.commands[l]) == 0:
            del Command.commands[l]
    
    @classmethod
    def unregister_commands(cls, *identifiers):
        """ Unregister items from Command based on their 'identifiers'
            (functionality or level/name). """
        for i in identifiers:
            _ = i.split("/", 1)
            try:
                l, n = _           # level, name
            except ValueError:
                f, n = _[0], None  # functionality
            # apply deletions
            if n is None:
                if f not in FUNCTIONALITIES:
                    raise ValueError("Non-existing functionality {}".format(f))
                _ = "../base/commands/" + f + ".py"
                _ = Path(__file__).parent.joinpath(_).resolve()
                for c in PyModulePath(str(_)).get_classes(Command):
                    Command.unregister_command(c)
            else:
                try:
                    c = Command.commands[l][n]
                    Command.unregister_command(c)
                except KeyError:
                    pass
    
    def complete_options(self):
        """ Default option completion method. """
        if self._nargs[0] > 0:
            return self.options or []
        return []
    
    def complete_values(self, option=None):
        """ Default value completion method. """
        if self._nargs[0] > 1:
            try:
                return self.values or []
            except:
                pass
        return []
    
    def validate(self, *args):
        """ Default validation method. """
        # first, check if the command has the splitargs flag, telling that the
        #  arguments should not be split (e.g. in the case of 'shell' where
        #  we don't want arguments to be parsed as they will be parsed by the OS
        if not self.splitargs:
            return
        # then, start checking the signature and, if relevant, validating
        #  options and arguments
        n_in = len(args)
        n, m = self._nargs
        if n_in < m or n_in > n:
            pargs = "from %d to %d" % (m, n) if n != m else "%d" % n
            raise TypeError("validate() takes %s positional argument%s but %d "
                            "were given" % (pargs, ["", "s"][n > 0], n_in))
        if n == 1:    # command format: COMMAND VALUE
            if n_in == 1 and hasattr(self, "values"):
                assert args[0] in self.values
        elif n == 2:  # command format: COMMAND OPTION VALUE
            if n_in > 0 and self.options is not None:
                assert args[0] in self.options
            if n_in == 2 and hasattr(self, "values"):
                assert args[1] in self.values

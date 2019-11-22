# -*- coding: UTF-8 -*-
import re
from inspect import getargspec

from .components.config import Config
from .entity import Entity, MetaEntity
from ..utils.misc import failsafe
from ..utils.objects import BorderlessTable
from ..utils.path import Path, PyModulePath

__all__ = ["Command"]

COMMAND_STYLES = [
    "lowercase",  # ClassName => classname
    "none",  # ClassName => ClassName
    "powershell",  # ClassName => Class-Name
    "slugified",  # ClassName => class-name
    "uppercase"  # ClassName => CLASSNAME
]
"""
Usage:
  >>> from sploitkit import Command
  >>> Command.set_style("powershell")
"""
FUNCTIONALITIES = [
    "general",  # commands for every level
    "utils",  # utility commands (for every level)
    "recording",  # recording commands (for every level)
    "root",  # base root-level commands
    "project",  # base project-level commands
    "module",  # base module-level commands
]


class MetaCommand(MetaEntity):
    """ Metaclass of a Command. """
    style = "slugified"

    def __init__(self, *args):
        argspec = getargspec(self.run)
        s, args, defs = "{}", argspec.args[1:], argspec.defaults
        for a in args[:len(args) - len(defs or [])]:
            s += " " + a
        if len(defs or []) > 0:
            s += " ["
            i = []
            for a, d in zip(args[len(args) - len(defs):], defs):
                i.append("{}={}".format(a, d) if d is not None else a)
            s += " ".join(i) + "]"
        self.signature = s
        self.args, self.defaults = args, defs

    def help(self, alias=None):
        """ Help message for the command. """
        return self.get_info(("name", "description"), "comments")

    @property
    def config(self):
        """ Shortcut to bound console's config instance. """
        try:
            return self.console.config
        except AttributeError:
            return Config()

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
    # convention: mangled attributes should not be customized when subclassing
    #              Command...
    _functionalities = FUNCTIONALITIES
    _levels = []
    # ... by opposition to public class attributes that can be tuned
    aliases = []
    alias_only = False
    commands = {}
    level = "general"
    except_levels = []
    single_arg = False

    @property
    def _nargs(self):
        """ Get run's signature info (n = number of args,
                                      m = number of args with no default). """
        argspec = getargspec(self.run)
        n = len(argspec.args) - 1  # substract 1 for self
        return n, n - len(argspec.defaults or ())

    @property
    def app_folder(self):
        """ Shortcut to the current application folder. """
        return self.console.app_folder

    @property
    def config(self):
        """ Shortcut to bound console's config instance. """
        return self.module.config if hasattr(self, "module") and \
                                     self.module is not None else \
            self.__class__.console.__class__.config

    @property
    def files(self):
        """ Shortcut to bound console's file manager instance. """
        return self.console.__class__._files

    @property
    def logger(self):
        """ Shortcut to bound console's logger instance. """
        return self.console.logger

    @property
    @failsafe
    def module(self):
        """ Shortcut to bound console's module class. """
        return self.console.module

    @property
    def modules(self):
        """ Shortcut to list of registered modules. """
        return self.console.modules

    @property
    def recorder(self):
        """ Shortcut to global command recorder. """
        return self.console.__class__._recorder

    @property
    def workspace(self):
        """ Shortcut to the current workspace. """
        return self.console.workspace

    @classmethod
    def check_applicability(cls):
        """ Check for Command's applicability. """
        _ = getattr(cls, "applies_to", [])
        return len(_) == 0 or not hasattr(cls, "console") or \
               cls.console.module.fullpath in _

    @classmethod
    def get_help(cls, *levels, **kwargs):
        """ Display commands' help(s), using its metaclass' properties. """
        if len(levels) == 0:
            levels = Command._levels
        if len(levels) == 2 and "general" in levels:
            # process a new dictionary of commands, handling levels in order
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
            if len(cmds) == 0 or l in kwargs.get('except_levels', []):
                continue
            d = [["Command", "Description"]]
            for n, c in sorted(cmds.items(), key=lambda x: x[0]):
                if not hasattr(c, "console") or not c.check():
                    continue
                d.append([n, getattr(c, "description", "")])
            t = BorderlessTable(d, "{} commands".format(l.capitalize()))
            s += t.table + "\n\n"
            i += 1
        return "\n" + s.strip() + "\n" if i > 0 else ""

    @classmethod
    def register_command(cls, subcls):
        """ Register the command and its aliases in a dictionary according to
             its level. """
        _ = subcls.level
        levels = [_] if not isinstance(_, (list, tuple)) else _
        for l in levels:
            Command.commands.setdefault(l, {})
            if l not in Command._levels:
                Command._levels.append(l)
            if not subcls.alias_only:
                Command.commands[l][subcls.name] = subcls
            for alias in subcls.aliases:
                Command.commands[l][alias] = subcls

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
        _ = subcls.level
        levels = [_] if not isinstance(_, (list, tuple)) else _
        n = subcls.name
        # remove every reference in commands dictionary
        for l in levels:
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
        for l in levels:
            if len(Command.commands[l]) == 0:
                del Command.commands[l]

    @classmethod
    def unregister_commands(cls, *identifiers):
        """ Unregister items from Command based on their 'identifiers'
            (functionality or level/name). """
        for i in identifiers:
            _ = i.split("/", 1)
            try:
                l, n = _  # level, name
            except ValueError:
                f, n = _[0], None  # functionality
            # apply deletions
            if n is None:
                if f not in cls._functionalities:
                    raise ValueError("Unknown functionality {}".format(f))
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

    def complete_keys(self):
        """ Default option completion method.
             (will be triggered if the number of run arguments is 2) """
        return getattr(self, "keys", []) or \
               list(getattr(self, "values", {}).keys())

    def complete_values(self, option=None):
        """ Default value completion method. """
        if self._nargs[0] == 1:
            if option is not None:
                raise TypeError("complete_values() takes 1 positional argument "
                                "but 2 were given")
            return getattr(self, "values", [])
        if self._nargs[0] == 2:
            return getattr(self, "values", {}).get(option)
        return []

    def validate(self, *args):
        """ Default validation method. """
        # check for the signature and, if relevant, validating keys and values
        n_in = len(args)
        n, m = self._nargs
        if n_in < m or n_in > n:
            pargs = "from %d to %d" % (m, n) if n != m else "%d" % n
            raise TypeError("validate() takes %s positional argument%s but %d "
                            "were given" % (pargs, ["", "s"][n > 0], n_in))
        if n == 1:  # command format: COMMAND VALUE
            l = self.complete_values()
            if n_in == 1 and len(l) > 0 and args[0] not in l:
                raise ValueError("invalid value")
        elif n == 2:  # command format: COMMAND OPTION VALUE
            l = self.complete_keys()
            if n_in > 0 and len(l) > 0 and args[0] not in l:
                raise ValueError("invalid key")
            l = self.complete_values(args[0])
            if n_in == 2 and len(l) > 0 and args[1] not in l:
                raise ValueError("invalid value")

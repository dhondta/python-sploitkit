from __future__ import unicode_literals

import os
import pathlib
import random
import re
import shlex
import string
from prompt_toolkit import print_formatted_text, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError

from .command import load_commands, Command
from .components import *
from .defaults import *
from .module import load_modules, Module
from ..utils.config import Config, Option
from ..utils.path import Path


__all__ = ["Console", "ConsoleExit"]


dcount = lambda d, n=0: sum([dcount(v, n) if isinstance(v, dict) else n + 1 \
                             for v in d.values()])


class Console(object):
    level = ROOT_LEVEL
    name = ""
    message = [
        ('class:prompt', " > "),
    ]
    motd = """
    
    """
    parent = None
    config = Config({
        Option('WORKSPACE', "folder where results are saved", True): "~/Notes",
        Option('APPLICATION_FOLDER', "folder where application assets (i.e."
                                     " logs) are saved", True): "~/.{name}",
    })
    recorder = Recorder()
    sources = {
        'banners':  None,
        'commands': COMMAND_SOURCES,
        'modules':  MODULE_SOURCES,
    }
    style = {
        '':        "#30b06f",
        'prompt':  "#eeeeee",
    }

    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.__init(**kwargs) if parent is None else self.__update()
        self.__setup()
        # setup the session with the custom completer and validator
        completer = CommandCompleter()
        completer.console = self
        validator = CommandValidator()
        validator.console = self
        self.__session = PromptSession(
            self.message,
            completer=completer,
            validator=validator,
            style=Style.from_dict(self.style),
        )
    
    def __init(self, **kwargs):
        """ Initialize the parent console with commands and modules. """
        if Console.parent is not None:
            raise Exception("Only one parent console can be used")
        Console.parent = self
        Console.appname = self.name
        # display a random banner from the banners folder
        get_banner_func = kwargs.get('get_banner_func', get_banner)
        print_formatted_text(get_banner_func(self._sources("banners")))
        # display a random quote from quotes.csv (in the banners folder)
        get_quote_func = kwargs.get('get_quote_func', get_quote)
        print_formatted_text(get_quote_func(self._sources("banners")))
        # setup modules
        kw = {'include_base': kwargs.get("include_base", True)}
        load_modules(*self._sources("modules"), **kw)
        self.modules = Module.modules
        for m in Module._subclasses:
            m.console = self
        nmod = dcount(self.modules)
        # load all commands
        if hasattr(self, "exclude"):
            kw['exclude'] = self.exclude
        load_commands(*self._sources("commands"), **kw)
        # TODO: display a MOTD (i.e. with nmod)
        # setup the prompt message
        self.message.insert(0, ('class:prompt', self.name))
    
    def __setup(self):
        """ Setup the console, i.e. logging and config options. """
        # setup level's commands
        self.commands = {}
        self.commands.update(Command.commands.get("general", {}))
        for n, c in list(self.commands.items()):
            if c.level == "general" and \
                self.level in getattr(c, "except_levels", []):
                del self.commands[n]
        self.commands.update(Command.commands.get(self.level, {}))
        for c in self.commands.values():
            c.console = self
        # expand format variables using console's attributes
        for k, d, v, r in self.config.items():
            kw = {}
            for n in re.findall(r'\{([a-z]+)\}', v):
                kw[n] = getattr(self, n, "")
            try:
                self.config[k] = v.format(**kw)
            except:
                continue
        # expand and resolve paths
        for k, d, v, r in self.config.items():
            if k.lower().endswith("folder") or k == "WORKSPACE":
                # this will ensure that every path is expanded
                p = Path(v, create=True, expand=True)
                self.config[k] = str(p)
                if not p.exists():
                    p.mkdir()
        # attach a logger to the console (if parent console)
        if self.parent is None:
            logspath = Path(self.config['APPLICATION_FOLDER']).joinpath("logs")
            if not logspath.exists():
                logspath.mkdir()
            logfile = str(logspath.joinpath(Console.appname + ".log"))
            self.logger = get_logger(self.name, logfile)
        else:
            self.logger = Console.parent.logger
    
    def __update(self):
        """ Update child console's prompt message and style. """
        # setup the prompt message by adding child's message tokens at the
        #  end of parent's one (parent's last token is then re-appended)
        m = [_ for _ in self.parent.message]
        t = m.pop()
        m.extend(self.message)
        m.append(t)
        self.message = m
        # setup the style, using this of the parent
        self.style.update(self.parent.style)
    
    def _sources(self, items):
        """ Return the list of sources for the related items
             [commands|modules|banners], first trying subclass' one then Console
             class' one. """
        try:
            return self.sources[items]
        except KeyError:
            return Console.sources[items]
    
    def execute(self, cmd, abort=False):
        """ Alias for run. """
        return self.run(cmd, abort)
    
    def run(self, cmd, abort=False):
        """ Run a framework console command. """
        cmd = cmd.strip()
        tokens = shlex.split(cmd)
        # assign tokens (or abort if tokens' split gives [])
        try:
            name, args = tokens[0], tokens[1:]
        except IndexError:  
            return True
        # create a command instance (or abort if name not in self.commands) ;
        #  if command arguments should not be split, adapt args
        try:
            obj = self.commands[name]()
            if not obj.splitargs:
                _ = cmd[len(name):].strip()
                args = (_, ) if len(_) > 0 else ()
        except KeyError:
            return True
        # now handle the command (and its validation if existing)
        try:
            if hasattr(obj, "validate"):
                obj.validate(*args)
            obj.run(*args)
            return True
        except ConsoleExit:
            return False
        except Exception as e:
            self.logger.exception(e)
            return abort is False
    
    def start(self):
        """ Start looping with console's session prompt. """
        while True:
            try:
                _ = self.__session.prompt(auto_suggest=AutoSuggestFromHistory())
                if not self.run(_):
                    return
                if self.recorder.enabled:
                    self.recorder.save(_)
            except EOFError:
                break
            except KeyboardInterrupt:
                continue


class ConsoleExit(Exception):
    """ Dedicated exception class for exiting a (sub)console. """
    pass

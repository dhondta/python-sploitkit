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
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError

from .command import load_commands, Command
from .components import *
from .defaults import *
from .module import load_modules, Module
from ..utils.config import Config, Option
from ..utils.meta import Entity, MetaEntity
from ..utils.path import Path


__all__ = ["Console", "ConsoleExit", "ConsoleDuplicate", "FrameworkConsole"]


dcount = lambda d, n=0: sum([dcount(v, n) if isinstance(v, dict) else n + 1 \
                             for v in d.values()])


def load_consoles():
    """ Initialize the list of Entity._subclasses[Console]. """
    # handle proxy classes exclusion ; this will remove classes like for example
    #  RootCommand which aims to define level="root" for related level commands
    for c in Console.subclasses:
        if len(c.__subclasses__()) > 0:
            Console.unregister_subclass(c)
        else:
            c.config.console = c


class Console(Entity, metaclass=MetaEntity):
    """ Base console class. """
    # convention: mangled attributes are not customizable when subclassing
    #              Console...
    _recorder = Recorder()
    # ... by opposition to public class attributes that can be tuned
    appname = ""
    config = Config()
    level = ROOT_LEVEL
    message = PROMPT_FORMAT
    motd = """
    
    """
    parent = None
    sources = SOURCES
    style = PROMPT_STYLE

    def __init__(self, parent=None, **kwargs):
        # determine the relevant parent
        self.parent = parent
        if self.parent is not None and self.parent.level == self.level:
            while parent is not None and parent.level == self.level:
                parent = parent.parent  # go up of one console level
            # raise an exception in the context of command's .run() execution,
            #  to be propagated to console's .run() execution, setting the
            #  directly higher level console in argument
            raise ConsoleDuplicate(parent)
        # configure the console regarding its parenthood
        if self.parent is None:
            if Console.parent is not None:
                raise Exception("Only one parent console can be used")
            Console.parent = self
            self.__init(**kwargs)
        self.config.normalize()
        self.reset()
        # setup the session with the custom completer and validator
        completer, validator = CommandCompleter(), CommandValidator()
        completer.console = validator.console = self  # console back-reference
        message, style = self.prompt
        self.__session = PromptSession(
            message,
            completer=completer,
            validator=validator,
            style=Style.from_dict(style),
        )
    
    def __init(self, **kwargs):
        """ Initialize the parent console with commands and modules. """
        # display a random banner from the banners folder
        get_banner_func = kwargs.get('get_banner_func', get_banner)
        print_formatted_text(get_banner_func(self._sources("banners")))
        # display a random quote from quotes.csv (in the banners folder)
        get_quote_func = kwargs.get('get_quote_func', get_quote)
        print_formatted_text(get_quote_func(self._sources("banners")))
        # setup modules
        kw = {'include_base': kwargs.get("include_base", True)}
        load_modules(*self._sources("modules"), **kw)
        for m in Module.subclasses:
            m.console = self
        nmod = dcount(self.modules)
        # load all commands
        if hasattr(self, "exclude"):
            kw['exclude'] = self.exclude
        load_commands(*self._sources("commands"), **kw)
        # load subconsole classes
        load_consoles()
        # TODO: display a MOTD (i.e. with nmod)
        # display module stats
        m = []
        for c in self.modules.keys():
            m.append("{} {}".format(len(self.modules[c]), c))
        if len(m) > 0:
            mlen = max(map(len, m))
            s = ""
            print("")
            for line in m:
                line = ("-=[ {: <" + str(mlen) + "} ]=-").format(line)
                print_formatted_text(FormattedText([("#00ff00", line)]))
            print("")
        # setup the prompt message
        self.message.insert(0, ('class:appname', self.appname))
    
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
    
    def reset(self):
        """ Setup commands for the current level and reset bindings between
             commands and the current console. """
        # bind console class attributes with the Console class
        self.__class__.config.console = self.__class__
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
        except ConsoleDuplicate as e:
            # pass the higher console instance attached to the exception raised
            #  from within a command's .run() execution to console's .start(),
            #  keeping the current command to be reexecuted
            raise ConsoleDuplicate(e.higher, cmd if e.cmd is None else e.cmd)
        except ConsoleExit:
            return False
        except Exception as e:
            self.logger.exception(e)
            return abort is False
    
    def start(self):
        """ Start looping with console's session prompt. """
        reexec = None
        while True:
            try:
                _ = reexec if reexec is not None else \
                    self.__session.prompt(auto_suggest=AutoSuggestFromHistory())
                reexec = None
                if not self.run(_):
                    return  # console run aborted
                if Console._recorder.enabled:
                    Console._recorder.save(_)
            except ConsoleDuplicate as e:
                if self == e.higher:  # stop raising duplicate when reaching a
                    reexec = e.cmd    #  console with a different level, then
                    self.reset()      #  reset associated commands not to rerun
                    continue          #  the erroneous command from the
                                      #  just-exited console
                self.logger.debug("Exiting {}[{}]".format(self.__class__, id(self)))
                raise e  # reraise up to the higher (level) console
            except EOFError:
                break
            except KeyboardInterrupt:
                continue
    
    @property
    def logger(self):
        try:
            return Console.logger
        except:
            return null_handler
    
    @property
    def modules(self):
        return Module.modules
    
    @property
    def prompt(self):
        if self.parent is None:
            return self.message, self.style
        # setup the prompt message by adding child's message tokens at the
        #  end of parent's one (parent's last token is then re-appended)
        pmessage, pstyle = self.parent.prompt
        message = pmessage.copy()  # copy parent message tokens
        t = message.pop()
        message.extend(self.message)
        message.append(t)
        # setup the style, using this of the parent
        style = pstyle.copy()  # copy parent style dict
        style.update(self.style)
        return message, style

    @classmethod
    def register_console(cls, subcls):
        """ Register console classes and link them with their configs. """
        subcls.config.console = subcls


class ConsoleDuplicate(Exception):
    """ Dedicated exception class for exiting a duplicate (sub)console. """
    def __init__(self, higher, cmd=None):
        self.cmd, self.higher = cmd, higher
        super(ConsoleDuplicate, self).__init__("Another console of the same "
                                               "level is already running")


class ConsoleExit(Exception):
    """ Dedicated exception class for exiting a (sub)console. """
    pass


class FrameworkConsole(Console):
    """ Framework console subclass for defining specific config options. """
    aliases = []
    config = Config({
        Option(
            'APP_FOLDER',
            "folder where application assets (i.e.  logs) are "
            "saved",
            True,
        ): "~/.{appname}",
        Option(
            'DEBUG',
            "debug mode",
            False,
            callback=lambda o: o.config.console._set_logging(o.value)
        ): "false",
        Option(
            'WORKSPACE',
            "folder where results are saved",
            True
        ): "~/Notes",
    })

    def __init__(self, *args, **kwargs):
        FrameworkConsole._set_logging(to_file=False)
        super(FrameworkConsole, self).__init__(*args, **kwargs)
    
    @classmethod
    def _set_logging(cls, debug=False, to_file=True):
        """ Set a new logger with the input logging level. """
        level = ["INFO", "DEBUG"][debug]
        logfile = None
        if to_file:
            # attach a logger to the console
            logspath = Path(cls.config.option('APP_FOLDER').value).joinpath("logs")
            logspath.mkdir(parents=True, exist_ok=True)
            logfile = str(logspath.joinpath(cls.appname + ".log"))
        Console.logger = get_logger(cls.name, logfile, level)

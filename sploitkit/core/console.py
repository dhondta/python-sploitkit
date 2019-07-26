# -*- coding: UTF-8 -*-
import gc
import os
import random
import re
import shlex
import string
from bdb import BdbQuit
from importlib import find_loader
from inspect import isfunction
from prompt_toolkit import print_formatted_text, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError
from shutil import move

from .command import *
from .components import *
from .entity import *
from .model import *
from .module import *
from ..utils.docstring import parse_docstring
from ..utils.misc import failsafe
from ..utils.path import Path


__all__ = [
    "Entity",
    # subclassable main entities
    "BaseModel", "Model", "StoreExtension",
    "Command",
    "Console",
    "Module",
    # console-related classes
    "Config", "ConsoleExit", "ConsoleDuplicate", "FrameworkConsole", "Option",
]

dcount = lambda d, n=0: sum([dcount(v, n) if isinstance(v, dict) else n + 1 \
                             for v in d.values()])


class Console(Entity, metaclass=MetaEntity):
    """ Base console class. """
    # convention: mangled attributes should not be customized when subclassing
    #              Console...
    _issues   = []
    _recorder = Recorder()
    _storage  = StoragePool(StoreExtension)
    # ... by opposition to public class attributes that can be tuned
    appname      = ""
    config       = Config()
    exclude      = []
    level        = ROOT_LEVEL
    message      = PROMPT_FORMAT
    motd         = """
    
    """
    parent       = None
    sources      = SOURCES
    style        = PROMPT_STYLE

    def __init__(self, parent=None, **kwargs):
        # determine the relevant parent
        self.parent = parent
        if self.parent is not None and self.parent.level == self.level:
            while parent is not None and parent.level == self.level:
                parent = parent.parent  # go up of one console level
            # raise an exception in the context of command's .run() execution,
            #  to be propagated to console's .run() execution, setting the
            #  directly higher level console in argument
            raise ConsoleDuplicate(self, parent)
        # configure the console regarding its parenthood
        if self.parent is None:
            if Console.parent is not None:
                raise Exception("Only one parent console can be used")
            Console.parent = self
            self.__init(**kwargs)
        else:
            self.parent.child = self
        self.reset()
        # setup the session with the custom completer and validator
        completer, validator = CommandCompleter(), CommandValidator()
        completer.console = validator.console = self
        message, style = self.prompt
        hpath = Path(self.config.option("WORKSPACE").value).joinpath("history")
        self._session = PromptSession(
            message,
            completer=completer,
            history=FileHistory(hpath),
            validator=validator,
            style=Style.from_dict(style),
        )
    
    def __init(self, **kwargs):
        """ Initialize the parent console with commands and modules. """
        bsrc = self._sources("banners")
        if bsrc is not None:
            # display a random banner from the banners folder
            get_banner_func = kwargs.get('get_banner_func', get_banner)
            banner_color = kwargs.get('banner_colorized_sections', ())
            text = get_banner_func(bsrc, banner_color)
            if text:
                print(text)
            # display a random quote from quotes.csv (in the banners folder)
            get_quote_func = kwargs.get('get_quote_func', get_quote)
            text = get_quote_func(bsrc)
            if text:
                print(text)
        # setup entities
        load_entities(
            [BaseModel, Command, Console, Model, Module, StoreExtension],
            *self._sources("entities"),
            include_base=kwargs.get("include_base", True),
            select=kwargs.get("select", {'command': Command._functionalities}),
            exclude=kwargs.get("exclude", {}),
            backref=kwargs.get("backref", BACK_REFERENCES),
            docstr_parser=kwargs.get("docstr_parser", parse_docstring),
        )
        Console._storage.models = Model.subclasses + BaseModel.subclasses
        # TODO: display a MOTD (i.e. with nmod)
        # display module stats
        m = []
        width = max(len(str(len(m))) for m in self.modules.values())
        for category in self.modules.keys():
            l = "{} {}".format(Module.get_count(category), category)
            disabled = Module.get_count(category, enabled=False)
            if disabled > 0:
                l += " ({} disabled)".format(disabled)
            m.append(l)
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
        # display warnings
        if len(Console._issues) > 0:
            self.logger.warning("There are some issues ; use 'show issues' to "
                                "see more details")
    
    def _close(self):
        """ Gracefully close the console. """
        self.logger.debug("Exiting {}[{}]".format(self.__class__.__name__,
                                                  id(self)))
        if hasattr(self, "close") and isfunction(self.close):
            self.close()
        # cleanup references for this console
        self.detach()
        if hasattr(self, "_session"):
            delattr(self._session.completer, "console")
            delattr(self._session.validator, "console")
        for k in [_ for _ in self.__dict__.keys()]:
            delattr(self, k)
        del self.__dict__
        if self.parent is not None:
            # rebind entities to the parent console
            self.parent.reset()
        else:
            # gracefully close every DB in the pool
            self._storage.free()
    
    def _get_tokens(self, text, suffix=("", "\"", "'")):
        """ Recursive token split function also handling ' and " (that is, when
             'text' is a partial input with a string not closed by a quote). """
        text = text.lstrip()
        try:
            tokens = shlex.split(text + suffix[0])
        except ValueError:
            return self._get_tokens(text, suffix[1:])
        except IndexError:
            return []
        if len(tokens) > 0:
            cmd = tokens[0]
            if len(tokens) > 2 and \
                getattr(self.commands.get(cmd), "single_arg", False):
                tokens = [cmd, " ".join(tokens[1:])]
            elif len(tokens) > 3:
                tokens = [cmd, tokens[1], " ".join(tokens[2:])]
        return tokens
    
    def _reset_logname(self):
        """ Reset logger's name according console's attributes. """
        try:
            self.logger.name = "{}:{}".format(self.level, self.logname)
        except AttributeError:
            self.logger.name = self.__class__.name
    
    def _sources(self, items):
        """ Return the list of sources for the related items
             [commands|modules|banners], first trying subclass' one then Console
             class' one. """
        try:
            return self.sources[items]
        except KeyError:
            return Console.sources[items]
    
    def attach(self, eccls, directref=False, backref=True):
        """ Attach an entity child to the calling entity's instance. """
        # handle direct reference from self to eccls
        if directref:
            # attach new class
            setattr(self, eccls.entity, eccls)
        # handle back reference from eccls to self
        if backref:
            setattr(eccls, self.__class__.entity, self)
    
    @failsafe
    def detach(self, eccls=None):
        """ Detach an entity child class from the console and remove its
             back-reference. """
        # if no argument, detech every class registered in self._attached
        if eccls is None:
            for subcls in Entity._subclasses:
                self.detach(subcls)
        elif eccls in ["command", "module"]:
            for ec in [Command, Module][eccls == "module"].subclasses:
                if ec.entity == eccls:
                    self.detach(ec)
        else:
            if hasattr(self, eccls.entity):
                delattr(self, eccls.entity)
            if hasattr(eccls, self.__class__.entity):
                delattr(eccls, self.__class__.entity)
    
    def execute(self, cmd, abort=False):
        """ Alias for run. """
        return self.run(cmd, abort)
    
    def reset(self):
        """ Setup commands for the current level, reset bindings between
             commands and the current console then update store's object. """
        self.detach("command")
        # bind console class attributes with the Console class
        self.__class__.config.console = self.__class__
        # setup level's commands, starting from general-purpose commands
        self.commands = {}
        self.commands.update(Command.commands.get("general", {}))
        for n, c in list(self.commands.items()):
            if c.level == "general" and \
                self.level in getattr(c, "except_levels", []):
                del self.commands[n]
        # add relevant commands from the specific level
        for n, c in Command.commands.get(self.level, {}).items():
            if c.check():
                self.commands[n] = c
        # now, attach the console with the commands
        for c in self.commands.values():
            self.attach(c)
        # get the relevant store and bind it to loaded models
        p = Path(self.config.option('WORKSPACE').value).joinpath("store.db")
        Console.store = Console._storage.get(p)
    
    def run(self, cmd, abort=False):
        """ Run a framework console command. """
        tokens = self._get_tokens(cmd)
        # assign tokens (or abort if tokens' split gives [])
        try:
            name, args = tokens[0], tokens[1:]
        except IndexError:
            return True
        # create a command instance (or abort if name not in self.commands) ;
        #  if command arguments should not be split, adapt args
        try:
            obj = self.commands[name]()
        except KeyError:
            return True
        # now handle the command (and its validation if existing)
        try:
            if hasattr(obj, "validate"):
                obj.validate(*args)
            obj.run(*args)
            return True
        except BdbQuit:  # when using pdb.set_trace()
            return True
        except ConsoleDuplicate as e:
            # pass the higher console instance attached to the exception raised
            #  from within a command's .run() execution to console's .start(),
            #  keeping the current command to be reexecuted
            raise ConsoleDuplicate(e.current, e.higher,
                                   cmd if e.cmd is None else e.cmd)
        except ConsoleExit:
            return False
        except Exception as e:
            self.logger.exception(e)
            return abort is False
        finally:
            gc.collect()
    
    def start(self):
        """ Start looping with console's session prompt. """
        reexec = None
        self._reset_logname()
        self.logger.debug("Starting {}[{}]".format(self.__class__.__name__,
                                                   id(self)))
        while True:
            self._reset_logname()
            try:
                _ = reexec if reexec is not None else \
                    self._session.prompt(auto_suggest=AutoSuggestFromHistory())
                reexec = None
                Console._recorder.save(_)
                if not self.run(_):
                    break  # console run aborted
            except ConsoleDuplicate as e:
                if self == e.higher:   # stop raising duplicate when reaching a
                    reexec = e.cmd     #  console with a different level, then
                    self.reset()       #  reset associated commands not to rerun
                    e.current._close() #  the erroneous command from the
                    continue           #  just-exited console
                self._close()
                raise e  # reraise up to the higher (level) console
            except EOFError:
                Console._recorder.save("exit")
                break
            except KeyboardInterrupt:
                continue
        self._close()
        return self

    @property    
    def issues(self):
        """ List issues for the console, its bound commands and module. """
        m = getattr(self, "module", None)
        l = [self.__class__] + [] if m is None else [m]
        l.extend(self.commands.values())
        t = ""
        for cls in l:
            for cls, subcls, errors in cls.get_issues():
                if value is None:
                    t += "{}: {}\n- ".format(cls, subcls)
                    t += "\n- ".join("[{}] {}".format(k, e) for k, err in \
                                     errors.items() for e in err) + "\n"
                else:
                    for k, e in errors.items():
                        if k == value:
                            t += "- {}/{}: {}\n".format(cls, subcls, e)
        return t + "\n"
    
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
    def __init__(self, current, higher, cmd=None):
        self.cmd, self.current, self.higher = cmd, current, higher
        super(ConsoleDuplicate, self).__init__("Another console of the same "
                                               "level is already running")


class ConsoleExit(Exception):
    """ Dedicated exception class for exiting a (sub)console. """
    pass


class FrameworkConsole(Console):
    """ Framework console subclass for defining specific config options. """
    _entity_class = Console
    aliases       = []
    config        = Config({
        Option(
            'APP_FOLDER',
            "folder where application assets (i.e. logs) are saved",
            True,
            callback=lambda o: move(o.old_value, o.value) \
                               if o.old_value != o.value else None,
        ): "~/.{appname}",
        Option(
            'DEBUG',
            "debug mode",
            False,
            bool,
            callback=lambda o: o.config.console._set_logging(o.value),
        ): "false",
        Option(
            'WORKSPACE',
            "folder where results are saved",
            True,
        ): "~/Notes",
        Option(
            'ENCRYPT_PROJECT',
            "ask for a password to encrypt a project when archiving",
            True,
            bool,
        ): "true",
    })

    def __init__(self, *args, **kwargs):
        self.__class__._set_logging()
        super(FrameworkConsole, self).__init__(*args, **kwargs)
    
    @classmethod
    def _set_logging(cls, debug=False, to_file=True):
        """ Set a new logger with the input logging level. """
        l, p = ["INFO", "DEBUG"][debug], None
        if to_file:
            # attach a logger to the console
            lpath = Path(cls.config.option('APP_FOLDER').value).joinpath("logs")
            # at this point, 'config' is not bound yet ; so {appname} will not
            #  be formatted in logfile
            p = Path(str(lpath).format(appname=cls.appname), create=True)
            p = str(p.joinpath("main.log"))
        Console.logger = get_logger(cls.name, p, l)

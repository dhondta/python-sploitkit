# -*- coding: UTF-8 -*-
import gc
import os
import shlex
import sys
from asciistuff import get_banner, get_quote
from bdb import BdbQuit
from datetime import datetime
from inspect import isfunction
from itertools import chain
from prompt_toolkit import print_formatted_text, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import ANSI, FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from .command import *
from .components import *
from .entity import *
from .model import *
from .module import *
from ..utils.docstring import parse_docstring
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


class MetaConsole(MetaEntity):
    """ Metaclass of a Console. """
    _has_config = True


class Console(Entity, metaclass=MetaConsole):
    """ Base console class. """
    # convention: mangled attributes should not be customized when subclassing
    #              Console...
    _files    = FilesManager()
    _jobs     = JobsPool()
    _recorder = Recorder()
    _sessions = None #FIXME: SessionsPool
    _state    = {}  # state shared between all the consoles
    _storage  = StoragePool(StoreExtension)
    # ... by opposition to public class attributes that can be tuned
    appname = ""
    config  = Config()
    exclude = []
    level   = ROOT_LEVEL
    message = PROMPT_FORMAT
    motd    = """
    
    """
    parent  = None
    sources = SOURCES
    style   = PROMPT_STYLE

    def __init__(self, parent=None, **kwargs):
        super(Console, self).__init__()
        # determine the relevant parent
        self.parent = parent
        if self.parent is not None and self.parent.level == self.level:
            while parent is not None and parent.level == self.level:
                parent = parent.parent  # go up of one console level
            # raise an exception in the context of command's .run() execution,
            #  to be propagated to console's .run() execution, setting the
            #  directly higher level console in argument
            raise ConsoleDuplicate(self, parent)
        # back-reference the console
        self.config.console = self
        # configure the console regarding its parenthood
        if self.parent is None:
            if Console.parent is not None:
                raise Exception("Only one parent console can be used")
            Console.parent = self
            Console.parent._start_time = datetime.now()
            Console.appdispname = Console.appname
            Console.appname = Console.appname.lower()
            self.__init(**kwargs)
        else:
            self.parent.child = self
        # reset commands and other bound stuffs
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
        CustomLayout(self)
    
    def __init(self, **kwargs):
        """ Initialize the parent console with commands and modules. """
        Console._dev_mode = kwargs.pop("dev", False)
        # setup banners
        bsrc = self._sources("banners")
        if bsrc is not None:
            print_formatted_text("")
            # display a random banner from the banners folder
            get_banner_func = kwargs.get('get_banner_func', get_banner)
            banner_colors = kwargs.get('banner_section_styles', {})
            text = get_banner_func(self.appdispname, bsrc, styles=banner_colors)
            if text:
                print_formatted_text(ANSI(text))
            # display a random quote from quotes.csv (in the banners folder)
            get_quote_func = kwargs.get('get_quote_func', get_quote)
            try:
                text = get_quote_func(os.path.join(bsrc, "quotes.csv"))
                if text:
                    print_formatted_text(ANSI(text))
            except ValueError:
                pass
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
        # setup libraries
        lsrc = self._sources("libraries")
        if lsrc is not None:
            if isinstance(lsrc, str):
                lsrc = [lsrc]
            if isinstance(lsrc, (list, tuple, set)):
                for lib in map(lambda p: os.path.abspath(p), lsrc[::-1]):
                    sys.path.insert(0, lib)
        # display module stats
        print_formatted_text(FormattedText([("#00ff00", Module.get_summary())]))
        # setup the prompt message
        self.message.insert(0, ('class:appname', self.appname))
        # display warnings
        if Entity.has_issues():
            self.logger.warning("There are some issues ; use 'show issues' to "
                                "see more details")
        # console's components back-referencing
        for attr in ["_files", "_jobs"]:
            setattr(getattr(Console, attr), "console", self)
    
    def _close(self):
        """ Gracefully close the console. """
        self.logger.debug("Exiting {}[{}]".format(self.__class__.__name__,
                                                  id(self)))
        if hasattr(self, "close") and isfunction(self.close):
            self.close()
        # cleanup references for this console
        self.detach()
        # important note: do not confuse '_session' (refers to prompt session)
        #                  with sessions (sessions manager)
        if hasattr(self, "_session"):
            delattr(self._session.completer, "console")
            delattr(self._session.validator, "console")
        # remove the singleton instance of the current console
        c = self.__class__
        if hasattr(c, "_instance"):
            del c._instance
        if self.parent is not None:
            del self.parent.child
            # rebind entities to the parent console
            self.parent.reset()
            # remove all finished jobs from the pool
            self._jobs.free()
        else:
            # gracefully close every DB in the pool
            self._storage.free()
            # terminate all running jobs
            self._jobs.terminate()
    
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
        """ Reset logger's name according to console's attributes. """
        try:
            self.logger.name = "{}:{}".format(self.level, self.logname)
        except AttributeError:
            self.logger.name = self.__class__.name
    
    def _run_if_defined(self, func):
        """ Run the given function if it is defined at the module level. """
        if hasattr(self, "module") and hasattr(self.module, func) and \
            not (getattr(self.module._instance, func)() is None):
            self.logger.debug("{} failed".format(func))
            return False
        return True

    def _sources(self, items):
        """ Return the list of sources for the related items
             [banners|entities|libraries], first trying subclass' one then
             Console class' one. """
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
            setattr(eccls, "console", self)
        # create a singleton instance of the entity
        eccls._instance = getattr(eccls, "_instance", None) or eccls()
    
    def detach(self, eccls=None):
        """ Detach an entity child class from the console and remove its
             back-reference. """
        # if no argument, detach every class registered in self._attached
        if eccls is None:
            for subcls in Entity._subclasses:
                self.detach(subcls)
        elif eccls in ["command", "module"]:
            for ec in [Command, Module][eccls == "module"].subclasses:
                if ec.entity == eccls:
                    self.detach(ec)
        else:
            if hasattr(eccls, "entity") and hasattr(self, eccls.entity):
                delattr(self, eccls.entity)
            # remove the singleton instance of the entity previously opened
            if hasattr(eccls, "_instance"):
                del eccls._instance
    
    def execute(self, cmd, abort=False):
        """ Alias for run. """
        return self.run(cmd, abort)
    
    def reset(self):
        """ Setup commands for the current level, reset bindings between
             commands and the current console then update store's object. """
        self.detach("command")
        # setup level's commands, starting from general-purpose commands
        self.commands = {}
        # add commands
        for n, c in chain(Command.commands.get("general", {}).items(),
                          Command.commands.get(self.level, {}).items()):
            self.attach(c)
            if self.level not in getattr(c, "except_levels", []) and c.check():
                self.commands[n] = c
            else:
                self.detach(c)
        root = self.config.option('WORKSPACE').value
        # get the relevant store and bind it to loaded models
        p = Path(root).joinpath("store.db")
        Console.store = Console._storage.get(p)
        # update command recorder's root directory
        self._recorder.root_dir = root
    
    def run(self, cmd, abort=False):
        """ Run a framework console command. """
        # assign tokens (or abort if tokens' split gives [])
        tokens = self._get_tokens(cmd)
        try:
            name, args = tokens[0], tokens[1:]
        except IndexError:
            return True
        # get the command singleton instance (or abort if name not in
        #  self.commands) ; if command arguments should not be split, adapt args
        try:
            obj = self.commands[name]._instance
        except KeyError:
            return True
        # now handle the command (and its validation if existing)
        try:
            if hasattr(obj, "validate"):
                obj.validate(*args)
            if name != "run" or self._run_if_defined("prerun"):
                obj.run(*args)
                if name == "run":
                    self._run_if_defined("postrun")
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
        except ValueError as e:
            if str(e).startswith("invalid width ") and \
               str(e).endswith(" (must be > 0)"):
                self.logger.warning("Cannot display ; terminal width too low")
            else:
                (self.logger.exception if self.config.option('DEBUG').value \
                 else self.logger.failure)(e)
            return abort is False
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
        # execute attached module's pre-load function if relevant
        self._run_if_defined("preload")
        # now start the console loop
        while True:
            self._reset_logname()
            try:
                _ = reexec if reexec is not None else \
                    self._session.prompt(
                        auto_suggest=AutoSuggestFromHistory(),
                        #bottom_toolbar="This is\na multiline toolbar",
                        # important note: this disables terminal scrolling
                        #mouse_support=True,
                    )
                reexec = None
                Console._recorder.save(_)
                if not self.run(_):
                    break  # console run aborted
            except ConsoleDuplicate as e:
                # stop raising duplicate when reaching a console with a 
                #  different level, then reset associated commands not to rerun
                #  the erroneous one from the context of the just-exited console
                if self == e.higher:   
                    reexec = e.cmd
                    self.reset()
                    continue
                self._close()
                # reraise up to the higher (level) console
                raise e
            except EOFError:
                Console._recorder.save("exit")
                break
            except (KeyboardInterrupt, ValueError):
                continue
        # execute attached module's post-load function if relevant
        self._run_if_defined("postload")
        # gracefully close and chain this console instance
        self._close()
        return self
    
    @property
    def logger(self):
        try:
            return Console.logger
        except:
            return null_logger
    
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
    
    @property
    def root(self):
        return Console.parent
    
    @property
    def state(self):
        """ Getter for the shared state. """
        return Console._state
    
    @property
    def uptime(self):
        """ Get application's uptime. """
        t = datetime.now() - Console.parent._start_time
        s = t.total_seconds()
        h, _ = divmod(s, 3600)
        m, s = divmod(_, 60)
        return "{:02}:{:02}:{:02}".format(int(h), int(m), int(s))


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
            set_callback=lambda o: o.root._set_app_folder(),
        ): "~/.{appname}",
        ROption(
            'DEBUG',
            "debug mode",
            False,
            bool,
            set_callback=lambda o: o.root._set_logging(o.value),
        ): "false",
        Option(
            'ENCRYPT_PROJECT',
            "ask for a password to encrypt a project when archiving",
            True,
            bool,
        ): "true",
        Option(
            'WORKSPACE',
            "folder where results are saved",
            True,
            set_callback=lambda o: o.root._set_workspace(),
        ): "~/Notes",
    })

    def __init__(self, appname=None, *args, **kwargs):
        Console.appname = appname or \
                          getattr(self, "appname", Console.appname)
        o, v = self.config.option('APP_FOLDER'), str(self.config['APP_FOLDER'])
        self.config[o] = Path(v.format(appname=self.appname.lower()))
        o.old_value = None
        # configure the file manager and the logger
        self._set_app_folder()
        super(FrameworkConsole, self).__init__(*args, **kwargs)
    
    def __set_folder(self, option, subpath=""):
        """ Set a new folder, moving an old to the new one if necessary. """
        o = self.config.option(option)
        old, new = o.old_value, o.value
        if old == new:
            return
        try:
            if old is not None:
                os.rename(old, new)
        except Exception as e:
            pass
        Path(new).joinpath(subpath).mkdir(parents=True, exist_ok=True)
        return new

    def _set_app_folder(self):
        """ Set a new APP_FOLDER, moving an old to the new one if necessary. """
        self._files.root_dir = self.__set_folder("APP_FOLDER", "files")
        self._set_logging()
    
    def _set_logging(self, debug=False, to_file=True):
        """ Set a new logger with the input logging level. """
        l, p = ["INFO", "DEBUG"][debug], None
        if to_file:
            # attach a logger to the console
            lpath = self.app_folder.joinpath("logs")
            lpath.mkdir(parents=True, exist_ok=True)
            p = str(lpath.joinpath("main.log"))
        Console.logger = get_logger(self.__class__.name, p, l)

    def _set_workspace(self):
        """ Set a new APP_FOLDER, moving an old to the new one if necessary. """
        self.__set_folder("WORKSPACE")
    
    @property
    def app_folder(self):
        """ Shortcut to the current application folder. """
        return Path(self.config.option('APP_FOLDER').value)
    
    @property
    def workspace(self):
        """ Shortcut to the current workspace. """
        return Path(self.config.option("WORKSPACE").value)

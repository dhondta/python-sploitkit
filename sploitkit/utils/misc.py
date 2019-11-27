# -*- coding: UTF-8 -*-
import logging
import os
from collections import MutableMapping
from shutil import which
from subprocess import call
from tempfile import TemporaryFile
from termcolor import colored


__all__ = ["catch_logger", "confirm", "edit_file", "failsafe", "flatten",
           "human_readable_size", "page_file", "page_text", "user_input"]


def catch_logger(f):
    """ Decoractor for catching the keyword-argument 'logger' and passing the
         logger to function's global scope. """
    def _wrapper(*a, **kw):
        logger = kw.pop("logger", None)
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger("root")
        f.__globals__['logger'] = logger
        return f(*a, **kw)
    return _wrapper


def confirm(txt="Are you sure ?", color=None):
    """ Ask for confirmation. """
    return user_input(txt, color=color, choices=("yes", "no"), default="no") \
           == "yes"


def edit_file(filename):
    """ Edit a file using Vim. """
    if which("vim") is None:
        raise OSError("vim is not installed")
    if not os.path.isfile(str(filename)):
        raise OSError("File does not exist")
    call(["vim", filename])


def failsafe(f):
    """ Simple decorator for catching every exception and returning None. """
    def __fw(s, *a, **kw):
        try:
            return f(s, *a, **kw)
        except:
            return
    return __fw


def flatten(d, parent_key="", sep="/"):
    """ Flatten a dictionary of dictionaries.
    See: https://stackoverflow.com/questions/6027558/flatten-nested-python-
         dictionaries-compressing-keys """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def human_readable_size(size, precision=0):
    """ Convert size in bytes to a more readable form. """
    i, units = 0, ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    while size > 1024 and i < len(units):
        i += 1
        size /= 1024
    return "%.*f%s" % (precision, size, units[i])


def page_file(*filenames):
    """ Page a list of files using Less. """
    filenames = list(map(str, filenames))
    for f in filenames:
        if not os.path.isfile(f):
            raise OSError("File does not exist")
    call(["less"] + filenames)


def page_text(text):
    """ Page a text using Less. """
    tmp = TemporaryFile()
    tmp.write(text)
    page_file(tmp.name)
    tmp.close()


def user_input(txt, color=None, choices=None, shortcuts=True, default=None):
    """ This helper function is aimed to simplify user input regarding
         raw_input() (Python 2.X) and input() (Python 3.Y).

    :param txt:       text to be displayed at prompt
    :param color:     to be used when displaying the prompt
    :param choices:   list of possible choices
    :param shortcuts: whether the first letter of each choice should be
                       considered as a shortcut for the choice
                       (if collisions, shortcuts are disabled)
    :param default:   default value to be considered at empty input
    :return:          user input
    """
    txt = txt.strip() + " "
    choices = None if not type(choices) in [list, tuple, set] or \
                      len(choices) == 0 else list(choices)
    # check for choices and shortcuts
    if choices is not None:
        if shortcuts and len(set(map(lambda x: x[0], choices))) == len(choices):
            _ = map(lambda x: "[" + x[0].upper() + "]" + x[1:], choices)
            txt += "({}) ".format("|".join(_))
            shortcuts = [x[0].lower() for x in choices]
        else:
            txt += "({}) ".format("|".join(choices))
            shortcuts = []
    # then mention the default value if relevant
    if default is not None and (choices is None or default in choices):
        txt += "[default: {}] ".format(default)
    # colorize the text if necessary
    txt = txt if color is None else colored(txt, color)
    # now, prompt for user input
    try:
        while True:
            try:
                user_input = raw_input(txt)
            except NameError:
                user_input = input(txt)
            if user_input.strip() == "" and default is not None:
                break
            if choices is None or user_input in choices or (shortcuts and \
                user_input[0].lower() + user_input[1:] in choices):
                return user_input
            if shortcuts and user_input.lower() in shortcuts:
                return choices[shortcuts.index(user_input.lower())]
    except KeyboardInterrupt:
        print("")
    return default

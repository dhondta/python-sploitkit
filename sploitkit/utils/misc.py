# -*- coding: UTF-8 -*-
import collections
import logging
from termcolor import colored


__all__ = ["catch_logger", "failsafe", "flatten", "user_input"]


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
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def user_input(txt="Are you sure ?", color=None,
               choices=("yes", "no"), default="no"):
    """ This helper function is aimed to simplify user input regarding
         raw_input() (Python 2.X) and input() (Python 3.Y).

    :param txt:   text to be displayed at prompt
    :param color: to be used when displaying the prompt
    :return:      user input
    """
    txt = txt.strip() + " "
    if choices is not None:
        txt += "({}) ".format("|".join(choices))
    if default is not None:
        txt += "[default: {}] ".format(default)
    txt = txt if color is None else colored(txt, color)
    choices = None if not type(choices) in [list, tuple, set] or \
                      len(choices) == 0 else choices
    try:
        while True:
            try:
                user_input = raw_input(txt)
            except NameError:
                user_input = input(txt)
            if user_input.strip() == "":
                break
            if choices is None or user_input in choices:
                return user_input == "yes" if user_input in ["yes", "no"] else \
                       user_input
    except KeyboardInterrupt:
        print("")
    return default == "yes" if default in ["yes", "no"] else default

from __future__ import unicode_literals

import collections


__all__ = ["failsafe", "flatten"]


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

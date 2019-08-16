# -*- coding: UTF-8 -*-
from inspect import isclass

from .path import Path


__all__ = ["ClassRegistry", "PathBasedDict"]


class ClassRegistry(dict):
    """ Custom dictionary class using class-based keys and list values. """
    def __iter__(self):
        """ Iter over subclasses of every registered class. """
        for l in self.values():
            for subcls in l:
                yield subcls
    
    def key(self, name):
        """ Get class-based key from its name. """
        for k in self.keys():
            if isclass(k) and k.__name__.lower() == name.lower():
                return k
    
    def value(self, key, name):
        """ Get class-based value from a list associated to a given key. """
        if not isclass(key):
            key = self.key(key)
        if key is not None:
            for v in self[key]:
                if isclass(v) and v.__name__.lower() == name.lower():
                    return v


class PathBasedDict(dict):
    """ Enhanced dictionary class. """
    def count(self, path=None, **kwargs):
        """ Count the number of leaf values under the given path of keys. """
        def _rcount(d=self, a=0):
            if isinstance(d, dict):
                for k, v in d.items():
                    a += _rcount(v)
            else:
                # when not a dict, we are at a leaf of the object tree, kwargs
                #  is then used as a set of criteria to be matched to include
                #  the object in the count
                a += 1 if len(kwargs) == 0 or \
                          all(getattr(d, attr, value) == value \
                          for attr, value in kwargs.items()) else 0
            return a
        return _rcount(self.rget(path))

    def rget(self, path=None):
        """ Find the subdictionary matching the given path of keys. """
        def _rget(p=path, d=self):
            p = Path(str(p))
            _ = p.parts
            return _rget(p.child, d[_[0]]) if len(_) > 1 else d[_[0]]
        return self if path is None else _rget()

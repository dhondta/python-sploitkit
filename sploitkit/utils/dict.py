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
    def __convert_path(self, path):
        """ Handle multiple path formats, e.g.:
            - "a/b/c/d"     (string)
            - Path("a/b/c/d")     (Path)
            - "a", "b", "c" (tuple of strings) """
        if not isinstance(path, tuple):
            path = (str(path), )
        return Path(*path).parts
    
    def __delitem__(self, path):
        """ Remove the item at the given path of subdictionaries. """
        d, parts = self, self.__convert_path(path)
        del self[parts[:-1]][parts[-1]]
        parts = parts[:-1]
        while len(parts) > 1 and len(d[parts]) == 0:
            del self[parts[:-1]][parts[-1]]
            parts = parts[:-1]
        if len(parts) == 1 and len(d[parts]) == 0:
            super(PathBasedDict, self).__delitem__(parts[0])
    
    def __getitem__(self, path):
        """ Get the item from the given path of subdictionaries. """
        d, parts = self, self.__convert_path(path)
        for p in parts:
            d = d.get(p)
        return d
    
    def __setitem__(self, path, value):
        """ Set the value to the given path of subdictionaries. """
        d, parts, curr = self, self.__convert_path(path), []
        for p in parts[:-1]:
            if not isinstance(d, dict):
                raise ValueError("Path at '{}' already owns a value"
                                 .format(str(Path(*curr))))
            d.setdefault(p, {})
            d = d[p]
            curr.append(p)
        if not isinstance(d, dict):
            raise ValueError("Path at '{}' already owns a value"
                             .format(str(Path(*curr))))
        d[parts[-1]] = value

    def count(self, path=None, **kwargs):
        """ Count the number of leaf values (given the attributes matching
             kwargs if any) under the given path of keys. """
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
        return _rcount(self[path])

# -*- coding: UTF-8 -*-
from collections import OrderedDict
from inspect import isclass
from time import time

from .path import Path


__all__ = ["merge_dictionaries",
           "ClassRegistry", "ExpiringDict", "PathBasedDict"]


def merge_dictionaries(*dictionaries, **kwargs):
    """ Merge dictionaries into the first given one, that is, merging child
         dictionaries and lists.
    
    :param update:     update with the latest encountered value
    :param duplicates: keep duplicates in lists and tuples
    """
    create_new = kwargs.get('create_new', False)
    update = kwargs.get('update', True)
    duplicates = kwargs.get('duplicates', False)
    d = {} if create_new else dictionaries[0]
    for dictionary in dictionaries[int(not create_new):]:
        for k, v in dictionary.items():
            if k not in d:
                d[k] = v
            elif not update:
                continue
            elif isinstance(v, dict):
                d[k] = merge_dictionaries(d[k], v, **kwargs)
            elif isinstance(v, (tuple, list)):
                l = list(d[k])
                for x in v:
                    if x in l and duplicates or x not in l:
                        l.append(x)
                if isinstance(v, tuple):
                    l = tuple(l)
                d[k] = l
            elif isinstance(v, set):
                for x in v:
                    d[k].add(x)
            else:
                d[k] = v
    return d


class ClassRegistry(dict):
    """ Custom dictionary class using class-based keys and list values. """
    def __iter__(self):
        """ Iter over subclasses of every registered class. """
        for l in self.values():
            for subcls in l:
                yield subcls
    
    def key(self, name):
        """ Get class-based key from its name. """
        if name is None:
            return
        for k in self.keys():
            if isclass(k) and k.__name__.lower() == name.lower():
                return k
    
    def value(self, key, name):
        """ Get class-based value from a list associated to a given key. """
        if not isclass(key):
            key = self.key(key)
        for k in (self.keys() if key is None else [key]):
            for v in self[k]:
                if isclass(v) and v.__name__.lower() == name.lower():
                    return v


class ExpiringDict(OrderedDict):
    """ Dictionary class with expiring keys, keeping these in chronological 
         order (regarding arrival or refresh if enabled). """
    def __init__(self, items=None, max_age=None, refresh=True, **kwargs):
        self.__locked = False
        self.__times = {}
        self.max_age = max_age
        self.refresh = refresh
        if isinstance(items, dict):
            for k, v in sorted(items.items(), key=lambda x: x[0]):
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v
    
    def __check_expiration(self, key):
        t = self.__times.get(key)
        if t is not None and time() - t > self.max_age:
            del self[key]
            return True
        return False
    
    def __cleanitems__(self):
        if self.__locked:
            return
        # remove heading expired items
        for key in list(self.keys()):
            if not self.__check_expiration(key):
                break
    
    def __delitem__(self, key):
        super(ExpiringDict, self).__delitem__(key)
        del self.__times[key]
    
    def __getattribute__(self, name):
        if not name.startswith("_ExpiringDict__") and not self.__locked and \
           not getattr(self, "_ExpiringDict__cleaned", False):
            self.__cleaned = True
            self.__cleanitems__()
            self.__cleaned = False
        return super(ExpiringDict, self).__getattribute__(name)
    
    def __setitem__(self, key, value):
        # keep new keys at the tail of the dictionary
        if self.get(key) is not None:
            del self[key]
        super(ExpiringDict, self).__setitem__(key, value)
        self.__times[key] = time()
    
    def __str__(self):
        return str(dict(**self))
    
    def lock(self):
        self.__locked = True
    
    def unlock(self):
        self.__locked = False


class PathBasedDict(dict):
    """ Enhanced dictionary class. """
    def __convert_path(self, path):
        """ Handle multiple path formats, e.g.:
            - "a/b/c/d"     (string)
            - Path("a/b/c/d")     (Path)
            - "a", "b", "c" (tuple of strings) """
        if not isinstance(path, tuple):
            path = (str(path),)
        path = tuple(filter(lambda x: x is not None, path))
        return Path(*path).parts
    
    def __delitem__(self, path):
        """ Remove the item at the given path of subdictionaries. """
        d, parts = self, self.__convert_path(path)
        if len(parts[:-1]) > 0:
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
        if isinstance(d, PathBasedDict):
            super(PathBasedDict, self).__setitem__(parts[-1], value)
        else:
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
                a += [0, 1][len(kwargs) == 0 or \
                            all(getattr(d, attr, value) == value \
                                for attr, value in kwargs.items())]
            return a
        return _rcount(self[path])

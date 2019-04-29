from __future__ import unicode_literals

import inspect
import re


__all__ = ["Entity", "MetaEntity"]


class Entity(object):
    """ Main class for a console entity (i.e. a command or a module). """
    @classmethod
    def iter_subclasses(cls):
        for subcls in cls._subclasses:
            yield subcls

    @classmethod
    def register_subclass(cls, subcls):
        if cls is not Entity:
            if not hasattr(cls, "_subclasses"):
                cls._subclasses = []
            cls._subclasses.append(subcls)
    
    @classmethod
    def run(self, *args, **kwargs):
        """ Generic method for running Entity's logic. """
        raise NotImplementedError("{}'s run() method is not implemented"
                                  .format(self.__name__))


class MetaEntity(type):
    """ Metaclass of an Entity, registering all its instances and defining some
         particular properties. """
    def __new__(meta, name, bases, clsdict, subcls=None):
        subcls = subcls or type.__new__(meta, name, bases, clsdict)
        for b in bases:
            for a in dir(b):
                m = getattr(b, a)
                if not callable(m) or not a.startswith("register_"):
                    continue
                m(subcls)
        return subcls

    @property
    def description(self):
        _ = re.split("\n\s*\n", (self.__doc__ or "").lstrip(), 1)[0]
        _ = re.sub(r'\s*\n\s*', " ", _)
        return _.strip().capitalize()
    
    @property
    def details(self):
        try:
            _ = re.split("\n\s*\n", (self.__doc__ or "").lstrip(), 1)[1]
            _ = re.sub(r'\s*\n\s*', " ", _)
            return _.strip().capitalize()
        except:
            return ""
    
    @property
    def name(self):
        _ = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', self.__name__)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', _).lower()

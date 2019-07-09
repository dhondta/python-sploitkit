from __future__ import unicode_literals

import inspect
import re


__all__ = ["Entity", "MetaEntity"]


class Entity(object):
    """ Main class for a console entity (i.e. a command or a module). """
    _fields = {
        'head': ["author", "reference", "source", "version"],
        'body': ["description"],
    }
    _subclasses = {}
    
    @classmethod
    def iter_subclasses(cls):
        for subcls in Entity._subclasses[cls]:
            yield subcls

    @classmethod
    def register_subclass(cls, subcls):
        """ Maintain a registry of subclasses inheriting from Entity. """
        bases = inspect.getmro(subcls)[:-1]  # drop <class 'object'> at index -1
        if bases[-1] is not Entity or (bases[-1] is Entity and len(bases) == 1)\
            or bases[-2] is subcls:
            return
        Entity._subclasses.setdefault(bases[-2], [])
        Entity._subclasses[bases[-2]].append(subcls)
        for f in Entity._fields['head']:
            # search for the given field in the docstring
            lines = (subcls.__doc__ or "").splitlines()
            for i, l in enumerate(lines):
                if f in l.lower():
                    # compute offset to field's value
                    o = l.lower().index(f) + len(f)
                    while l[o] in ": ":
                        o += 1
                    value = l[o:]
                    # search for split lines
                    j = i + 1
                    while i < len(lines) and lines[j].startswith(" " * o):
                        value += lines[j][o:]
                        j += 1
                    setattr(subcls, f, value.strip())
    
    @classmethod
    def run(self, *args, **kwargs):
        """ Generic method for running Entity's logic. """
        raise NotImplementedError("{}'s run() method is not implemented"
                                  .format(self.__name__))

    @classmethod
    def unregister_subclass(cls, subcls):
        """ Remove an entry from the registry of subclasses. """
        if cls in Entity._subclasses.keys():
            try:
                Entity._subclasses[cls].remove(subcls)
            except ValueError:
                pass


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
    def info(self):
        """ Display module's metadata and other information. """
        s = []
        for f in Entity._fields['head']:
            if getattr(self, f, None) is not None:
                s.append("\t{}: {}".format(f.capitalize(), getattr(self, f)))
        for f in Entity._fields['body']:
            if getattr(self, f, None) is not None:
                s.append("\n" + f)
        return "" if len(s) == 0 else "\n" + "\n".join(s) + "\n"
    
    @property
    def name(self):
        _ = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', self.__name__)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', _).lower()
    
    @property
    def subclasses(self):
        return Entity._subclasses[self]

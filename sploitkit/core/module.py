# -*- coding: UTF-8 -*-
from inspect import getfile

from .entity import Entity, MetaEntity
from ..utils.config import Config
from ..utils.dict import PathBasedDict
from ..utils.misc import failsafe, flatten
from ..utils.objects import BorderlessTable, NameDescription as NDescr
from ..utils.path import Path


__all__ = ["Module"]

#TODO: association of a module to a set of specific commands (not module-level)


class MetaModule(MetaEntity):
    """ Metaclass of a Module. """
    def __new__(meta, name, bases, clsdict):
        subcls = type.__new__(meta, name, bases, clsdict)
        # compute module's path
        if not hasattr(subcls, "path") or subcls.path is None:
            p = Path(getfile(subcls)).parent
            # collect the source temporary attribute
            s = getattr(subcls, "_source", ".")
            try:
                subcls.path = str(p.relative_to(Path(s)))
            except ValueError:
                subcls.path = None
        # then pass the subclass with its freshly computed path attribute to the
        #  original __new__ method, for registration in subclasses and in the
        #  list of modules
        super(MetaModule, meta).__new__(meta, name, bases, clsdict, subcls)
        return subcls
    
    @property
    def base(self):
        """ Module's category. """
        return str(Path(self.fullpath).child)
    
    @property
    def category(self):
        """ Module's category. """
        return str(Path(self.path).parts[0])
    
    @property
    def fullpath(self):
        """ Full path of the module, that is, its path joined with its name. """
        return str(Path(self.path).joinpath(self.name))
    
    @property
    def help(self):
        """ Help message for the module, formatted as a row with its name and 
             description then its list of options. """
        t = str(BorderlessTable(self.options))
        if len(t) > 0:
            t = "\n\n" + t
        return str(NDescr(self.name, self.description, self.details)) + t
    
    def search(self, text):
        """ Search for text in module's attributes. """
        return any(text in v for v in self._metadata.values())


class Module(Entity, metaclass=MetaModule):
    """ Main class handling console modules. """
    modules = PathBasedDict()
    
    @property
    @failsafe
    def logger(self):
        """ Module console-bound logger (shorcut). """
        return self.console.logger
    
    @property
    @failsafe
    def store(self):
        """ Module console-bound store (shorcut). """
        return self.console.store
    
    @classmethod
    def get_count(cls, path=None, **attrs):
        """ Count the number of modules under the given path and matching
             attributes. """
        return cls.modules.rcount(path, **attrs)

    @classmethod
    def get_help(cls, category=None):
        """ Display command's help, using its metaclass' properties. """
        _ = cls.modules
        categories = _.keys() if category is None else [category]
        s, i = "", 0
        for c in categories:
            d = [["Name", "Path", "Enabled", "Description"]]
            for n, m in sorted(flatten(_.get(c, {})).items(),
                               key=lambda x: x[0]):
                d.append([m.name, m.path, ["N", "Y"][m.enabled], m.description])
            t = BorderlessTable(d, "{} modules".format(c.capitalize()))
            s += t.table + "\n\n"
            i += 1
        return "\n" + s.strip() + "\n" if i > 0 else ""
    
    @classmethod
    def get_list(cls):
        """ Get the list of modules' fullpath. """
        return sorted([m.fullpath for m in Module.subclasses if m._applicable \
                                                            and m._enabled])
    
    @classmethod
    def get_modules(cls, path=None):
        """ Get the subdictionary of modules matching the given path. """
        return cls.modules.rget(path)

    @classmethod
    def register_module(cls, subcls):
        """ Register a Module subclass to the dictionary of modules. """
        if subcls.path is None:
            return  # do not consider orphan modules
        d = cls.modules
        for p in Path(subcls.path).parts:
            d.setdefault(p, {})
            d = d[p]
        d[subcls.name] = subcls

# -*- coding: UTF-8 -*-
from inspect import getfile

from .entity import Entity, MetaEntity
from ..utils import *
from ..utils.dict import PathBasedDict


__all__ = ["Module"]


class MetaModule(MetaEntity):
    """ Metaclass of a Module. """
    _has_config = True
    
    def __new__(meta, name, bases, clsdict):
        subcls = type.__new__(meta, name, bases, clsdict)
        # compute module's path from its root folder if no path attribute
        #  defined on its class
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
        return str(Path(self.fullpath).child) if self.category != "" else \
               self.name
    
    @property
    def category(self):
        """ Module's category. """
        try:
            return str(Path(self.path).parts[0])
        except IndexError:
            return ""
    
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
        nd = NameDescription(self.name, self.description)
        return str(nd) + t
    
    def search(self, text):
        """ Search for text in module's attributes. """
        return any(text in "".join(v).lower() for v in self._metadata.values())


class Module(Entity, metaclass=MetaModule):
    """ Main class handling console modules. """
    modules = PathBasedDict()
    
    @property
    def files(self):
        """ Shortcut to bound console's file manager instance. """
        return self.console.__class__._files
    
    @property
    def logger(self):
        """ Shortcut to bound console's logger instance. """
        return self.console.logger
    
    @property
    def store(self):
        """ Shortcut to bound console's store instance. """
        return self.console.store
    
    @property
    def workspace(self):
        """ Shortcut to the current workspace. """
        return self.console.workspace
    
    @classmethod
    def get_count(cls, path=None, **attrs):
        """ Count the number of modules under the given path and matching
             attributes. """
        return cls.modules.count(path, **attrs)

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
        return cls.modules[path]

    @classmethod
    def register_module(cls, subcls):
        """ Register a Module subclass to the dictionary of modules. """
        if subcls.path is None:
            return  # do not consider orphan modules
        cls.modules[subcls.path, subcls.name] = subcls

    @classmethod
    def unregister_module(cls, subcls):
        """ Unregister a Module subclass from the dictionary of modules. """
        del cls.modules[subcls.path, subcls.name]
        Module.subclasses.remove(subcls)

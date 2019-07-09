from __future__ import unicode_literals

import inspect

from ..utils.config import Config
from ..utils.meta import Entity, MetaEntity
from ..utils.misc import failsafe, flatten
from ..utils.objects import BorderlessTable, NameDescription
from ..utils.path import Path, PyFolderPath


__all__ = ["Module"]

#TODO: association of a module to a set of specific commands (not module-level)


def load_modules(*sources, **kwargs):
    """ Load every Module subclass found in the given source folders.
    
    :param sources:      paths (either with ~, relative or absolute) to folders
                          containing Module subclasses
    :param include_base: include the base commands provided with sploitkit
    """
    sources = list(sources)
    if kwargs.get("include_base", True):
        # this allows to use sploitkit.base modules for starting a project with
        #  a baseline of modules
        _ = Path(__file__).parent.joinpath("../base/modules/").resolve()
        sources.insert(0, str(_))
    for source in sources:
        try:
            source = str(Path(source).expanduser().resolve())
        except OSError:  # e.g. when the folder does not exist
            continue
        # bind the source to the Module main class as, when MetaModule.__new__
        #  is called, the source is not passed from the PyFolderPath to child
        #  PyModulePath instances ; this way, the module path can be determined
        Module._source = source
        # now, it loads every Python module from the list of source folders ;
        #  when loading Module subclasses, these are registered to 
        #  Module.modules and Module.subclasses for further direct access
        #  (i.e. from the console)
        PyFolderPath(source)
    try:
        delattr(Module, "_source")  # then clean up the temporary attribute
    except AttributeError:  # i.e. if sources list is empty (when include_base
        pass                #  is False)


class CustomDict(dict):
    def rget(self, path):
        def _rget(p=path, d=self):
            p = Path(str(p))
            _ = p.parts
            return _rget(p.child, d[_[0]]) if len(_) > 1 else d[_[0]]
        return _rget()


class MetaModule(MetaEntity):
    """ Metaclass of a Module. """
    def __new__(meta, name, bases, clsdict):
        subcls = type.__new__(meta, name, bases, clsdict)
        # compute module's path
        if not hasattr(subcls, "path") or subcls.path is None:
            p = Path(inspect.getfile(subcls)).parent
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
        return str(NameDescription(self.name, self.description, self.details)) \
               + t
    
    @property
    def options(self):
        """ Table of module options. """
        if hasattr(self, "config") and isinstance(self.config, Config):
            data = [["Name", "Value", "Description"]]
            for k, d, v in sorted(self.config.items(), key=lambda x: x[0]):
                data.append([k, v, d])
            return data
    
    def search(self, text):
        """ Search for text in module's attributes. """
        return any(text in x for x in [
            self.name,
            self.description,
            self.details,
            self.fullpath,
            self.category
        ])


class Module(Entity, metaclass=MetaModule):
    """ Main class handling console modules. """
    modules = CustomDict()
    
    @property
    @failsafe
    def logger(self):
        """ Module console-bound logger (shorcut). """
        return self.console.logger
    
    @property
    @failsafe
    def options(self):
        """ Module options (shorcut). """
        return self.config.keys()

    @classmethod
    def get_help(cls, category=None):
        """ Display command's help, using its metaclass' properties. """
        _ = cls.modules
        categories = _.keys() if category is None else [category]
        s, i = "", 0
        for c in categories:
            d = [["Name", "Path", "Description"]]
            for n, m in sorted(flatten(_.get(c, {})).items(),
                               key=lambda x: x[0]):
                d.append([m.name, m.path, m.description])
            t = BorderlessTable(d, "{} modules".format(c.capitalize()))
            s += t.table + "\n\n"
            i += 1
        return "\n" + s.strip() + "\n" if i > 0 else ""
    
    @classmethod
    def get_list(cls):
        """ Get the list of modules' fullpath. """
        return sorted([m.fullpath for m in Module.subclasses])
    
    @classmethod
    def get_modules(cls, path):
        """ Recursively get a subdictionary of the list of modules or a Module
             subclass from its full path. """
        def _rget(p=path, d=cls.modules):
            p = Path(str(p))
            _ = p.parts
            return _rget(p.child, d[_[0]]) if len(_) > 1 else d[_[0]]
        return _rget()

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

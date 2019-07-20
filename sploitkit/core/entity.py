from __future__ import unicode_literals

import gc
import re
from importlib import find_loader
from inspect import getfile, getmro
from shutil import which

from ..utils.dict import ClassRegistry
from ..utils.path import *


__all__ = ["load_entities", "Entity", "MetaEntity", "MetaEntityBase"]

ENTITIES = []
ent_id = lambda c: (getattr(c, "__file__", getfile(c)), c.__name__)


def load_entities(entities, *sources, **kwargs):
    """ Load every entity class of the given type found in the given source
         folders.
    
    :param sources:       paths (either with ~, relative or absolute) to folders
                           containing entity subclasses
    :param include_base:  include the base entities provided with the package
    :param select:        selected modules in the source folder
    :param exclude:       list of entity identifiers (in custom format, or
                           simply the entity class) to be excluded (useful when
                           including the base but not every entity is required)
    :param backref:       list of attributes to get entity's class to be bound to
    :param docstr_parser: user-defined docstring parser for populating metadata
    """
    global ENTITIES
    ENTITIES = [e.__name__ for e in entities]
    sources = list(sources)
    if kwargs.get("include_base", True):
        # this allows to use sploitkit.base for starting a project with a
        #  baseline of entities
        for n in ENTITIES:
            n = n.lower()
            for m in kwargs.get("select", {}).get(n, [""]):
                m = "../base/{}s/".format(n) + m + [".py", ""][m == ""]
                _ = Path(__file__).parent.joinpath(m).resolve()
                sources.insert(0, str(_))
    # now load every single source (folder of modules or single module)
    for source in sources:
        try:
            source = str(Path(source).expanduser().resolve())
        except OSError:  # e.g. when the folder does not exist
            continue
        # bind the source to the entity main class as, when MetaEntity.__new__
        #  is called, the source is not passed from the PyFolderPath to child
        #  PyModulePath instances ; this way, the entity path can be determined
        for e in entities:
            e._source = source
        # now, it loads every Python module from the list of source folders ;
        #  when loading entity subclasses, these are registered to entity's
        #  registry for further use (i.e. from the console)
        PyModulePath(source) if source.endswith(".py") else PyFolderPath(source)
    for e in entities:
        # clean up the temporary attribute
        try:
            delattr(e, "_source")
        except AttributeError:  # i.e. if sources list is empty (when include_base
            pass                #  is False)
        # remove proxy classes
        n = e.__name__.lower()
        for c in e.subclasses:
            if len(c.__subclasses__()) > 0:
                getattr(e, "unregister_{}".format(n),
                        Entity.unregister_subclass)(c)
        # handle specific entities or sets of entities exclusions ; this will
        #  remove them from Entity's registries
        excludes = kwargs.get("exclude", {}).get(n)
        if excludes is not None:
            getattr(e, "unregister_{}s".format(n),
                    Entity.unregister_subclasses)(*excludes)
        # handle conditional entities ; this will remove entities having a
        #  "condition" and/or a "check" method returning False
        for c in e.subclasses:
            try:
                c, o = c, c()
            except TypeError:
                break
            # convention: conditional entities are unregistered and removed
            if hasattr(o, "condition") and not o.condition():
                getattr(e, "unregister_{}".format(n),
                        Entity.unregister_subclass)(c)
            # convention: entities with missing requirements are disabled
            if hasattr(o, "check"):
                c._enabled = o.check()
            # populate metadata
            c._metadata = kwargs.get("docstr_parser", lambda s: {})(self)
            for attr in ["meta", "metadata"]:
                if hasattr(c, attr):
                    c._metadata.update(getattr(c, attr))
                    delattr(c, attr)
        # bind entity's subclasses to the given attributes for back-reference
        backrefs = kwargs.get("backref", {}).get(n)
        if backrefs is not None:
            for c in e.subclasses:
                for a, bn in backrefs:
                    bc = list(filter(lambda _: _.__name__.lower() == bn,
                                     entities))[0]
                    if a == "":
                        setattr(c, bn, bc)
                    elif getattr(c, a, None):
                        setattr(getattr(c, a), bn, bc)
    # then trigger garbage collection (for removed classes)
    gc.collect()


class Entity(object):
    """ Generic Entity class (i.e. a command or a module). """
    _enabled = True
    _fields     = {
        'head': ["author", "reference", "source", "version"],
        'body': ["description"],
    }
    _subclasses = ClassRegistry()
    
    @property
    def enabled(self):
        """ Boolean indicating if the entity is enabled. """
        return self.__class__._enabled
    
    @classmethod
    def check(cls):
        """ Check for module's requirements. """
        errors = {}
        for k, v in getattr(cls, "requirements", {}).items():
            if k == "file":
                for filepath in v:
                    if not Path(filepath).exists():
                        errors.setdefault("file", [])
                        errors["file"].append(filepath)
                        cls._enabled = False
            elif k == "python":
                for module in v:
                    if isinstance(module, tuple):
                        module, package = module
                    else:
                        package = module
                    if find_loader(module) is None:
                        errors.setdefault("python", [])
                        errors["python"].append(package)
                        cls._enabled = False
            elif k == "system":
                for tool in v:
                    if isinstance(tool, tuple):
                        tool, package = tool
                    else:
                        package = tool
                    if which(tool) is None:
                        errors.setdefault("system", [])
                        errors["system"].append(package)
                        cls._enabled = False
            else:
                raise ValueError("Unknown requirement type '{}'".format(k))
        if len(errors) > 0:
            cls._errors = errors
            return False
        else:
            return True
    
    @classmethod
    def get_class(cls, name):
        """ Get a class (key) from _subclasses by name (useful when the related
             class is not imported in the current scope). """
        return Entity._subclasses.key(name)

    @classmethod
    def get_subclass(cls, key, name):
        """ Get a subclass (value) from _subclasses by name (useful when the
             related class is not imported in the current scope). """
        return Entity._subclasses.value(key, name)

    @classmethod
    def register_subclass(cls, subcls):
        """ Maintain a registry of subclasses inheriting from Entity. """
        bases = list(getmro(subcls))
        # do not register if no list of entities yet
        if len(ENTITIES) == 0:
            return
        # do not register non-entity classes
        while len(bases) > 0 and bases[-1] is not Entity:
            bases.pop()
        if len(bases) <= 2:
            return
        # do not register base entities
        if subcls.__name__ in ENTITIES:
            return
        # get the base entity class
        ecls = [c for c in bases if c.__name__ in ENTITIES][0]
        Entity._subclasses.setdefault(ecls, [])
        # now register the subcls, ensured to be an end-subclass of the entity,
        #  avoiding duplicates (based on the source path and the class name)
        if ent_id(subcls) not in list(map(ent_id, Entity._subclasses[ecls])):
            # the following line is necessary because of the issue with
            #  inspect.getfile when multiple classes with the same name are
            #  imported from different modules ; this way, __file__ attribute
            #  (not attached by default for a class) is checked first before
            #  trying getfile(...)
            subcls.__file__ = getfile(subcls)
            Entity._subclasses[ecls].append(subcls)
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

    @classmethod
    def unregister_subclasses(cls, *subclss):
        """ Remove entries from the registry of subclasses. """
        for subcls in subclss:
            cls.unregister_subclass(subcls)


class MetaEntityBase(type):
    """ Metaclass of an Entity, registering all its instances. """
    def __new__(meta, name, bases, clsdict, subcls=None):
        subcls = subcls or type.__new__(meta, name, bases, clsdict)
        for b in bases:
            for a in dir(b):
                m = getattr(b, a)
                if callable(m) and any(a == "register_{}".format(w.lower()) \
                    for w in ["subclass"] + ENTITIES):
                    m(subcls)
        return subcls
    
    @property
    def subclasses(self):
        return Entity._subclasses.get(self, [])


class MetaEntity(MetaEntityBase):
    """ Metaclass of an Entity, adding some particular properties. """
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
    def enabled(self):
        """ Boolean indicating if the entity class is enabled. """
        return self._enabled

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

# -*- coding: UTF-8 -*-
import gc
import re
from importlib import find_loader
from inspect import getfile, getmro
from shutil import which

from .components.config import Config, Option
from ..utils.dict import ClassRegistry
from ..utils.objects import BorderlessTable, NameDescription as NDescr
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
                if _.exists():
                    sources.insert(0, str(_))
    # now load every single source (folder of modules or single module)
    for s in sources:
        source = Path(s).expanduser().resolve()
        if not source.exists():
            continue
        # bind the source to the entity main class as, when MetaEntity.__new__
        #  is called, the source is not passed from the PyFolderPath to child
        #  PyModulePath instances ; this way, the entity path can be determined
        for e in entities:
            e._source = str(source)
        # now, it loads every Python module from the list of source folders ;
        #  when loading entity subclasses, these are registered to entity's
        #  registry for further use (i.e. from the console)
        PyModulePath(source) if source.suffix == ".py" else PyFolderPath(source)
    for e in entities:
        # clean up the temporary attribute
        try:
            delattr(e, "_source")
        except AttributeError:  # i.e. if sources list is empty (when include_base
            pass                #  is False)
        # remove proxy classes
        n = e.__name__.lower()
        for c in e.subclasses[:]:
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
            c._metadata = kwargs.get("docstr_parser", lambda s: {})(c)
            # "meta" or "metadata" attributes will have precedence on the docstr
            for attr in ["meta", "metadata"]:
                if hasattr(c, attr):
                    c._metadata.update(getattr(c, attr))
                    delattr(c, attr)
            # if the metadata has options, create the config object
            for option in c._metadata.pop("options", []):
                try:
                    name, default, required, description = option
                except ValueError:
                    raise ValueError("Bad option ; should be (name, default, "
                                     "required, description)")
                if not hasattr(c, "config"):
                    c.config = Config()
                c.config[Option(name, description, required)] = default
            # dynamically declare properties for each metadata field
            for attr, value in c._metadata.items():
                # let the precedence to already existing attributes
                try:
                    getattr(c, attr)
                except AttributeError:
                    setattr(c, attr, value)
        # bind entity's subclasses to the given attributes for back-reference
        backrefs = kwargs.get("backref", {}).get(n)
        if backrefs is not None:
            for c in e.subclasses:
                for br in backrefs:
                    try:
                        a, bn = br
                    except ValueError:
                        a, bn = None, br[0] if isinstance(br, tuple) else br
                    bc = list(filter(lambda _: _.__name__.lower() == bn,
                                     entities))[0]
                    if a is None:
                        setattr(c, bn, bc)
                    elif getattr(c, a, None):
                        setattr(getattr(c, a), bn, bc)
    # then trigger garbage collection (for removed classes)
    gc.collect()


class BadSource(Exception):
    """ Custom exception for handling bad entity source. """
    pass


class Entity(object):
    """ Generic Entity class (i.e. a command or a module). """
    _applicable = True
    _enabled    = True
    _fields     = {
        'head': ["author", "reference", "source", "version"],
        'body': ["description"],
    }
    _metadata   = {}
    _subclasses = ClassRegistry()
    
    def __getattribute__(self, name):
        if name == "config" and getattr(self.__class__, "_has_config", False):
            c = self.__class__.config
            if hasattr(self, "parent") and self.parent is not None and \
                self.parent is not self:
                c += self.parent.config
            return c
        return super().__getattribute__(name)
    
    @property
    def applicable(self):
        """ Boolean indicating if the entity is applicable to the current
             context (i.e. of attached entities). """
        return self.__class__._applicable
    
    @property
    def base_class(self):
        """ Shortcut for accessing the Entity class, for use instead of __base__
             which only leads to the direct base class. """
        return Entity
    
    @property
    def enabled(self):
        """ Boolean indicating if the entity is enabled (i.e. if it has no
             missing requirement. """
        return self.__class__._enabled
    
    @property
    def issues(self):
        """ List issues encountered while checking entities. """
        return self.__class__.issues
    
    @classmethod
    def check(cls, other_cls=None):
        """ Check for entity's requirements. """
        cls = other_cls or cls
        cls._enabled = True
        errors = {}
        # check for requirements
        req = getattr(cls, "check_requirements", None)
        if req is not None:
            cls._enabled = cls.check_requirements()
        # FIXME: handle requirement in string ;
        #   e.g. {'system': "test"} will give issues 't', 'e', 's', 't' not
        #                            installed
        for k, v in getattr(cls, "requirements", {}).items():
            if k == "config":
                for opt, exp_val in v.items():
                    try:
                        o = cls.config.option(opt.upper())
                    except KeyError:
                        cls._enabled = False
                        break
                    o._reset = True
                    cur_val = o.value       # current value
                    if cur_val != exp_val:  # expected value
                        cls._enabled = False
                        break
            elif k == "file":
                for fpath in v:
                    if not Path(cls.__file__).parent.joinpath(fpath).exists():
                        errors.setdefault("file", [])
                        errors["file"].append(fpath)
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
            #elif k == "state":
            #    for key in v:
            #        if ...
            # FIXME: get the reference to Console class for Console._state and
            #         check if the state key is defined
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
        cls._errors = errors
        # check for applicability
        a = getattr(cls, "applies_to", [])
        if len(a) > 0:
            cls._applicable = False
            chk = getattr(cls, "check_applicability", None)
            if chk is not None:
                cls._applicable = cls.check_applicability()
            else:
                for _ in getattr(cls, "applies_to", []):
                    _, must_match, value = list(_[:-1]), _[-1], cls
                    while len(_) > 0:
                        value = getattr(value, _.pop(0), None)
                    if value and value == must_match:
                        cls._applicable = True
                        break
        return cls._enabled and cls._applicable
    
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
        # get the base entity class
        ecls = subcls._entity_class
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
    
    def run(self, *args, **kwargs):
        """ Generic method for running Entity's logic. """
        raise NotImplementedError("{}'s run() method is not implemented"
                                  .format(self.__class__.__name__))


class MetaEntityBase(type):
    """ Metaclass of an Entity, registering all its instances. """
    def __new__(meta, name, bases, clsdict, subcls=None):
        subcls = subcls or type.__new__(meta, name, bases, clsdict)
        if len(ENTITIES) > 0:
            mro_bases = list(getmro(subcls))
            # do not register non-entity classes or base entities
            while len(mro_bases) > 0 and mro_bases[-1] is not Entity:
                mro_bases.pop()
            if len(mro_bases) <= 2 or subcls.__name__ in ENTITIES:
                return subcls
            # set the base entity class
            ecls = [c for c in mro_bases if c.__name__ in ENTITIES][0]
            subcls._entity_class = ecls
            # trigger class registration
            for b in bases:
                for a in dir(b):
                    m = getattr(b, a)
                    if callable(m) and any(a == "register_{}".format(w.lower())\
                        for w in ["subclass"] + ENTITIES):
                        m(subcls)
        return subcls
    
    @property
    def subclasses(self):
        """ List of all classes of the current entity. """
        return Entity._subclasses.get(self, [])


class MetaEntity(MetaEntityBase):
    """ Metaclass of an Entity, adding some particular properties. """    
    def __getattribute__(self, name):
        if name == "config" and getattr(self, "_has_config", False):
            return self.__dict__.get("config", Config()) + \
                   (getattr(self.__base__, "config", Config()) \
                    if self.__base__ else Config())
        return super().__getattribute__(name)

    @property
    def applicable(self):
        """ Boolean indicating if the entity is applicable to the current
             context (i.e. of attached entities). """
        self.check()
        return self._applicable
    
    @property
    def enabled(self):
        """ Boolean indicating if the entity is enabled (i.e. if it has no
             missing requirement. """
        self.check()
        return self._enabled
    
    @property
    def entity(self):
        """ Normalized base entity name. """
        return self._entity_class.__name__.lower()
    
    @property
    def issues(self):
        """ List issues encountered while checking all the entities. """
        for cls, l in Entity._subclasses.items():
            for subcls in l:
                if hasattr(subcls, "_errors") and len(subcls._errors) > 0:
                    yield cls.__name__, subcls.__name__, subcls._errors
    
    @property
    def name(self):
        """ Normalized entity subclass name. """
        _ = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', self.__name__)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', _).lower()
    
    @property
    def options(self):
        """ Table of entity options. """
        if hasattr(self, "config") and isinstance(self.config, Config):
            data = [["Name", "Value", "Required", "Description"]]
            for n, d, v, r in sorted(self.config.items(), key=lambda x: x[0]):
                if v is None or n == v:
                    data.append([n, v, ["N", "Y"][r], d])
            return data
    
    def get_info(self, *fields, show_all=False):
        """ Display entity's metadata and other information. """
        t = ""
        if len(fields) == 0:
            fields = [("name", "description"),
                      ("author", "version", "comments"),
                      ("options", )]
        # make a data table with the given fields and corresponding values
        data, __used = [], []
        _ = lambda s: s.capitalize() + ":"
        for field in fields:
            if not isinstance(field, (list, tuple)):
                field = (field, )
            add_blankline = False
            for f in field:
                try:
                    f, alias = f.split("|", 1)
                except:
                    alias = f
                __used.append(f)
                v = getattr(self, f, "undefined")
                if v is None or len(v) == 0:
                    continue
                elif isinstance(v, (list, tuple)):
                    v = "- " + "\n- ".join(v)
                data.append([_(alias), v])
                add_blankline = True
            if add_blankline:
                data.append(["", ""])
        t = BorderlessTable(data, header=False).table + "\n" if len(data) > 0 \
            else ""
        # add other metadata if relevant
        if show_all:
            unused = set(self._metadata.keys()) - set(__used)
            if len(unused) > 0:
                t += self.get_info(*sorted(list(unused)))
        return t.rstrip() + "\n\n"
    
    def get_issues(self):
        """ List issues for self's entity. """
        if hasattr(self, "_errors") and len(self._errors) > 0:
            yield self.entity, self.__name__, self._errors

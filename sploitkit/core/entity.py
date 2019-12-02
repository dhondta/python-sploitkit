# -*- coding: UTF-8 -*-
import gc
import re
import sys
from collections import OrderedDict
from importlib.util import find_spec
from inspect import getfile, getmro
from shutil import which

from .components.config import Config, Option, ProxyConfig
from ..utils.dict import merge_dictionaries, ClassRegistry
from ..utils.objects import BorderlessTable
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
    :param backref:       list of attrs to get entity's class to be bound to
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
    # include the launcher script itself to include the subclassed console
    sources.insert(0, str(Path(sys.argv[0]).resolve()))
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
        tbr = []
        # clean up the temporary attribute
        if hasattr(e, "_source"):
            delattr(e, "_source")
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
        #  "condition" method returning False
        for c in e.subclasses[:]:
            # convention: conditional entities are unregistered and removed
            if hasattr(c, "condition") and not c().condition():
                getattr(e, "unregister_{}".format(n),
                        Entity.unregister_subclass)(c)
        # now populate metadata for each class
        for c in e.subclasses:
            set_metadata(c, kwargs.get("docstr_parser", lambda s: {}))
        # bind entity's subclasses to the given attributes for back-reference
        backrefs = kwargs.get("backref", {}).get(n)
        if backrefs is not None:
            for c in e.subclasses:
                for br in backrefs:
                    try:
                        a, bn = br  # [a]ttribute, [b]ackref [n]ame
                    except ValueError:
                        a, bn = None, br[0] if isinstance(br, tuple) else br
                    bc = list(filter(lambda _: _.__name__.lower() == bn,
                                     entities))[0]  # [b]ackref [c]lass
                    v = lambda: bc._instance
                    if a and getattr(c, a, None):
                        c = getattr(c, a)
                    setattr(c, bn, v)
    # then trigger garbage collection (for removed classes)
    gc.collect()


def set_metadata(c, docstr_parser):
    """ Set the metadata for an entity class given a docstring parser.
    
    :param c:             entity subclass
    :param docstr_parser: parsing function, taking 'c' as its input
    """
    # populate metadata starting by parsing entity class' docstring
    c._metadata = docstr_parser(c)
    # "meta" or "metadata" attributes then have precedence on the docstr
    #  (because of .update())
    for a in ["meta", "metadata"]:
        if hasattr(c, a):
            c._metadata.update(getattr(c, a))
            delattr(c, a)
    # if the metadata has options, create the config object
    for o in c._metadata.pop("options", []):
        try:
            name, default, required, description = o
        except ValueError:
            raise ValueError("Bad option ; should be (name, default, "
                             "required, description)")
        c.config[Option(name, description, required)] = default
    # dynamically declare properties for each metadata field
    for attr, value in c._metadata.items():
        # let the precedence to already existing attributes
        if attr not in c.__dict__.keys():
            setattr(c, attr, value)
    # add inherited entity classes' metadata
    b = c.__base__
    if b and getattr(c, "_inherit_metadata", False):
        for b in c.__bases__:
            if b is Entity:
                continue
            set_metadata(b, docstr_parser)
            for k, v in b._metadata.items():
                if k not in c._metadata.keys():
                    c._metadata[k] = v


class BadSource(Exception):
    """ Custom exception for handling bad entity source. """
    pass


class Entity(object):
    """ Generic Entity class (i.e. a command or a module). """
    _applicable = True
    _enabled    = True
    _metadata   = {}
    _subclasses = ClassRegistry()
    
    def __getattribute__(self, name):
        if name == "config" and getattr(self.__class__, "_has_config", False):
            c = ProxyConfig(self.__class__.config)
            # merge parent config if relevant
            if hasattr(self, "parent") and self.parent is not None and \
                self.parent is not self:
                c += self.parent.config
            # back-reference the entity
            setattr(c, self.__class__.entity, self)
            return c
        return super(Entity, self).__getattribute__(name)
    
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
    def cname(self):
        """ Subclass name. """
        return self.__class__.__name__
    
    @property
    def enabled(self):
        """ Boolean indicating if the entity is enabled (i.e. if it has no
             missing requirement. """
        return self.__class__.enabled
    
    @classmethod
    def check(cls, other_cls=None):
        """ Check for entity's requirements. """
        cls = other_cls or cls
        if cls is Entity:
            something_went_wrong = False
            for sc in Entity._subclasses:
                something_went_wrong = something_went_wrong or not sc.check()
            return something_went_wrong
        cls._enabled = True
        errors = {}
        # check for requirements
        req = getattr(cls, "check_requirements", None)
        if req is not None:
            cls._enabled = cls.check_requirements()
        for k, v in getattr(cls, "requirements", {}).items():
            if isinstance(v, str):
                v = [v]
            if k == "config":
                if not isinstance(v, dict):
                    raise ValueError("Bad config requirements")
                for opt, exp_val in v.items():
                    try:
                        o = cls.config.option(opt.upper())
                    except KeyError:
                        cls._enabled = False
                        break
                    cur_val = o.value       # current value
                    if cur_val != exp_val:  # expected value
                        cls._enabled = False
                        break
            elif k == "file":
                if not isinstance(v, (list, tuple, set)):
                    raise ValueError("Bad file requirements")
                for fpath in v:
                    if not Path(cls.__file__).parent.joinpath(fpath).exists():
                        errors.setdefault("file", [])
                        errors["file"].append(fpath)
                        cls._enabled = False
            elif k == "python":
                if not isinstance(v, (list, tuple, set)):
                    raise ValueError("Bad python requirements")
                for module in v:
                    if isinstance(module, tuple):
                        module, package = module
                        found = find_spec(module, package)
                    else:
                        package = module
                        found = find_spec(module)
                    if found is None:
                        errors.setdefault("python", [])
                        errors["python"].append(package)
                        cls._enabled = False
            elif k == "state":
                if isinstance(v, (list, tuple, set)):
                    skeys = {sk: None for sk in v}
                elif isinstance(v, dict):
                    skeys = v
                else:
                    raise ValueError("Bad state requirements")
                # catch Console from Entity's registered subclasses as Console
                #  cannot be imported in this module (cfr circular import)
                Console = cls.get_class("Console")
                _tmp = []
                for sk, sv in skeys.items():
                    # check if the state key exists
                    if sk not in Console._state.keys():
                        _tmp.append(sk)
                    # check if the value (if defined) matches
                    elif sv is not None:
                        cs = Console._state[sk]
                        # special case: state value is a dict
                        if isinstance(sv, dict) and isinstance(cs, dict):
                            check_key, _ = True, list(sv.items())
                            if len(_) == 1 and _[0][0] is None:
                                check_key = False
                            # case 1: classical dict
                            if check_key:
                                for ssk, ssv in sv.items():
                                    if ssk not in cs.keys() or cs[ssk] != ssv:
                                        _tmp.append("{}={}".format(sk, sv))
                                        break
                            # case 2: {None: value}, meaning that we expect to
                            #         find 'value' at least once for any key
                            else:
                                if _[0][1] not in cs.values():
                                    _tmp.append("{}?{}".format(sk, _[0][1]))
                                    break
                        # exact match between any other type than dict
                        else:
                            if sv != Console._state[sk]:
                                _tmp.append("{}={}".format(sk, sv))
                if len(_tmp) > 0:
                    errors.setdefault("state", [])
                    errors['state'].extend(_tmp)
                    cls._enabled = False
            elif k == "system":
                for tool in v:
                    _ = tool.split("/")
                    if len(_) == 1:
                        package = None
                    elif len(_) == 2:
                        package, tool = _
                    else:
                        raise ValueError("Bad system requirements")
                    if which(tool) is None:
                        if package is None:
                            errors.setdefault("tools", [])
                            errors["tools"].append(tool)
                        else:
                            errors.setdefault("packages", [])
                            errors["packages"].append(package)
                        cls._enabled = False
            else:
                raise ValueError("Unknown requirements type '{}'".format(k))
        cls._errors = errors
        # check for applicability
        cls._applicable = True
        a = getattr(cls, "applies_to", [])
        if len(a) > 0:
            cls._applicable = False
            chk = getattr(cls, "check_applicability", None)
            if chk is not None:
                cls._applicable = cls.check_applicability()
            else:
                # format: ("attr1", "attr2", ..., "attrN", "value")
                #   e.g.: ("module", "fullpath", "my/module/do_something")
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
    def get_info(cls, *fields, show_all=False):
        """ Display entity's metadata and other information.
        
        :param fields:   metadata fields to be output
        :param show_all: also include unselected fields, to be output behind the
                          list of selected fields
        """
        t = ""
        if len(fields) == 0:
            fields = [("name", "description"),
                      ("author", "email", "version", "comments"),
                      ("options",)]
        # make a data table with the given fields and corresponding values
        data, __used = [], []
        _ = lambda s: s.capitalize() + ":"
        for field in fields:
            if not isinstance(field, (list, tuple)):
                field = (field,)
            add_blankline = False
            for f in field:
                try:
                    f, alias = f.split("|", 1)
                except:
                    alias = f
                __used.append(f)
                v = getattr(cls, f, "")
                if v is None or len(v) == 0:
                    continue
                elif isinstance(v, (list, tuple)):
                    data.append([_(alias), v[0]])
                    for i in v[1:]:
                        data.append(["", i])
                else:
                    data.append([_(alias), v])
                add_blankline = True
            if add_blankline:
                data.append(["", ""])
        t = BorderlessTable(data, header=False).table + "\n" if len(data) > 0 \
            else ""
        # add other metadata if relevant
        if show_all:
            unused = set(cls._metadata.keys()) - set(__used)
            if len(unused) > 0:
                t += cls.get_info(*sorted(list(unused)))
        return t.rstrip() + "\n"
    
    @classmethod
    def get_issues(cls, subcls_name=None, category=None):
        """ List issues as a text. """
        # message formatting function
        def msg(scname, key, item):
            subcls = Entity.get_subclass(None, scname)
            m = getattr(subcls, "requirements_messages", {}) \
                .get(key, {}).get(re.split(r"(\=|\?)", item, 1)[0])
            if m is not None:
                return m.format(item)
            if key == "file":
                return "'{}' not found".format(item)
            elif key == "packages":
                return "'{}' system package is not installed".format(item)
            elif key == "python":
                return "'{}' Python package is not installed".format(item)
            elif key == "tools":
                return "'{}' tool is not installed".format(item)
            elif key == "state":
                item = re.split(r"(\=|\?)", item, 1)
                if len(item) == 1:
                    return "'{}' state key is not defined".format(item[0])
                elif item[1] == "=":
                    return "'{}' state key does not match the expected " \
                           "value '{}'".format(item[0], item[2])
                elif item[1] == "?":
                    return "'{}' state key is expected to have value '{}'" \
                           " at least once".format(item[0], item[2])
        # list issues using the related class method
        t = "\n"
        d = OrderedDict()
        for cname, scname, errors in Entity.issues(subcls_name, category):
            e = str(errors)
            d.setdefault(e, {})
            d[e].setdefault(cname, [])
            d[e][cname].append(scname)
        for _, names in d.items():
            errors = list(Entity.issues(list(names.values())[0][0]))[0][-1]
            t = ""
            for cname, scnames in names.items():
                cname += ["", "s"][len(scnames) > 1]
                t += "{}: {}\n- ".format(cname, ", ".join(sorted(scnames)))
                t += "\n- ".join(msg(scname, k, e) for k, err in errors.items()\
                                                   for e in err) + "\n"
        return "" if t.strip() == "" else t

    @classmethod
    def get_subclass(cls, key, name):
        """ Get a subclass (value) from _subclasses by name (useful when the
             related class is not imported in the current scope). """
        return Entity._subclasses.value(key, name)
    
    @classmethod
    def has_issues(cls, subcls_name=None, category=None):
        """ Tell if issues were encountered while checking entities. """
        try:
            next(iter(cls.issues(subcls_name, category)))
            return True
        except StopIteration:
            return False
    
    @classmethod
    def issues(cls, subcls_name=None, category=None):
        """ List issues encountered while checking all the entities. """
        cls.check()
        for cls, l in Entity._subclasses.items() if cls is Entity else \
                      cls.subclasses if cls in Entity._subclasses.keys() \
                      else [(cls._entity_class, [cls])]:
            for subcls in l:
                e = {}
                for b in subcls.__bases__:
                    # do not consider base classes without the issues method
                    #  (e.g. mixin classes)
                    if not hasattr(b, "issues"):
                        continue
                    # break when at parent entity level
                    if b in Entity._subclasses.keys() or b is Entity:
                        break
                    # update the errors dictionary starting with proxy classes
                    for _, __, errors in b.issues(category=category):
                        for c, i in errors.items():
                            e.setdefault(c, [])
                            e[c].extend(i)
                # now update the errors dictionary of the selected subclass
                if hasattr(subcls, "_errors") and len(subcls._errors) > 0:
                    for c, i in subcls._errors.items():
                        if category in [None, c]:
                            e.setdefault(c, [])
                            e[c].extend(i)
                if len(e) > 0:
                    for c, i in e.items():  # [c]ategory, [i]ssues
                        e[c] = list(sorted(set(i)))
                    n = subcls.__name__
                    if subcls_name in [None, n]:
                        yield cls.__name__, n, e

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
        # back-reference the entity from its config if existing
        if getattr(cls, "_has_config", False):
            setattr(subcls.config, "_" + subcls.entity,
                    lambda: subcls._instance)

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
            if "config" not in self.__dict__:
                setattr(self, "config", Config())
            c = self.__dict__['config']
            # back-reference the entity
            if hasattr(self, "_instance"):
                setattr(c, self.entity, self._instance)
            c = ProxyConfig(c)
            if hasattr(self, "_entity_class"):
                for b in self.__bases__:
                    if b == self._entity_class:
                        break
                    _ = getattr(b, "config", None)
                    if _:
                        c += _
            return c
        elif name in ["requirements", "requirements_messages"]:
            r = {}
            if hasattr(self, "_entity_class"):
                for b in self.__bases__[::-1]:
                    if b == self._entity_class:
                        break
                    merge_dictionaries(r, getattr(b, name, {}))
            merge_dictionaries(r, self.__dict__.get(name, {}))
            return r
        return super(MetaEntity, self).__getattribute__(name)
    
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

# -*- coding: UTF-8 -*-
import gc
import re
from collections import OrderedDict
from importlib.util import find_spec
from inspect import getfile, getmro
from shutil import which
from tinyscript.helpers import is_dict, is_function, is_list, is_str, merge_dict, parse_docstring, \
                               BorderlessTable, ClassRegistry, Path, PythonPath

from .components.config import Config, Option, ProxyConfig
from .components.logger import get_logger


__all__ = ["load_entities", "Entity", "MetaEntity", "MetaEntityBase"]

ENTITIES = []
logger = get_logger("core.entity")


def load_entities(entities, *sources, **kwargs):
    """ Load every entity class of the given type found in the given source folders.
    
    :param sources:       paths (either with ~, relative or absolute) to folders containing entity subclasses
    :param include_base:  include the base entities provided with the package
    :param select:        selected modules in the source folder
    :param exclude:       list of entity identifiers (in custom format, or simply the entity class) to be excluded
                           (useful when including the base but not every entity is required)
    :param backref:       list of attrs to get entity's class to be bound to
    :param docstr_parser: user-defined docstring parser for populating metadata
    :param remove_cache:  remove Python file cache
    """
    global ENTITIES
    ENTITIES = [e.__name__ for e in entities]
    sources = list(sources)
    if kwargs.get("include_base", True):
        # this allows to use sploitkit.base for starting a project with a baseline of entities
        for n in ENTITIES:
            n = n.lower()
            for m in kwargs.get("select", {}).get(n, [""]):
                m = f"../base/{n}s/" + m + [".py", ""][m == ""]
                p = Path(__file__).parent.joinpath(m).resolve()
                if p.exists():
                    sources.insert(0, p)
    # load every single source (folder of modules or single module)
    for s in sources:
        if not s.exists():
            logger.debug("Source does not exist: %s" % s)
            continue
        # bind the source to the entity main class
        for e in entities:
            e._source = str(s)
        # now, it loads every Python module from the list of source folders ; when loading entity subclasses, these are
        #  registered to entity's registry for further use (i.e. from the console)
        logger.debug("Loading Python source: %s" % s)
        # important note: since version 1.23.17 of Tinyscript, support for cached compiled Python files has been added,
        #                  for the PythonPath class, therefore influencing the location path of loaded entities (that
        #                  is, adding __pycache__)
        PythonPath(s, remove_cache=kwargs.get("remove_cache", False))
    for e in entities:
        tbr = []
        # clean up the temporary attribute
        if hasattr(e, "_source"):
            delattr(e, "_source")
        # remove proxy classes
        n = e.__name__.lower()
        for c in e.subclasses[:]:
            if len(c.__subclasses__()) > 0:
                getattr(e, "unregister_%s" % n, Entity.unregister_subclass)(c)
        # handle specific entities or sets of entities exclusions ; this will remove them from Entity's registries
        excludes = kwargs.get("exclude", {}).get(n)
        if excludes is not None:
            getattr(e, "unregister_%ss" % n, Entity.unregister_subclasses)(*excludes)
        # handle conditional entities ; this will remove entities having a "condition" method returning False
        for c in e.subclasses[:]:
            # convention: conditional entities are unregistered and removed
            if hasattr(c, "condition") and not c().condition():
                getattr(e, "unregister_%s" % n, Entity.unregister_subclass)(c)
        # now populate metadata for each class
        for c in e.subclasses:
            set_metadata(c, kwargs.get("docstr_parser", parse_docstring))
        # bind entity's subclasses to the given attributes for back-reference
        backrefs = kwargs.get("backref", {}).get(n)
        if backrefs is not None:
            for c in e.subclasses:
                for br in backrefs:
                    try:
                        a, bn = br  # [a]ttribute, [b]ackref [n]ame
                    except ValueError:
                        a, bn = None, br[0] if isinstance(br, tuple) else br
                    bc = list(filter(lambda _: _.__name__.lower() == bn, entities))[0]  # [b]ackref [c]lass
                    if a and getattr(c, a, None):
                        c = getattr(c, a)
                    setattr(c, bn, lambda: bc._instance)
    # then trigger garbage collection (for removed classes)
    gc.collect()


def set_metadata(c, docstr_parser):
    """ Set the metadata for an entity class given a docstring parser.
    
    :param c:             entity subclass
    :param docstr_parser: parsing function, taking 'c' as its input
    """
    # populate metadata starting by parsing entity class' docstring
    c._metadata = docstr_parser(c)
    # "meta" or "metadata" attributes then have precedence on the docstr (because of .update())
    for a in ["meta", "metadata"]:
        if hasattr(c, a):
            c._metadata.update(getattr(c, a))
            try:
                delattr(c, a)
            except AttributeError:
                pass  # occurs when class 'c' has no 'meta' anymore, but its base class well
    # if the metadata has options, create the config object
    for o in c._metadata.pop("options", []):
        try:
            name, default, required, description = o
        except ValueError:
            raise ValueError("Bad option ; should be (name, default, required, description)")
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
            if hasattr(self, "parent") and self.parent is not None and self.parent is not self:
                c += self.parent.config
            # back-reference the entity
            setattr(c, self.__class__.entity, self)
            return c
        return super(Entity, self).__getattribute__(name)
    
    @property
    def applicable(self):
        """ Boolean indicating if the entity is applicable to the current context (i.e. of attached entities). """
        return self.__class__._applicable
    
    @property
    def base_class(self):
        """ Shortcut for accessing Entity, for use instead of __base__ which only leads to the direct base class. """
        return Entity
    
    @property
    def cname(self):
        """ Subclass name. """
        return self.__class__.__name__
    
    @property
    def enabled(self):
        """ Boolean indicating if the entity is enabled (i.e. if it has no missing requirement. """
        return self.__class__.enabled
    
    @classmethod
    def check(cls, other_cls=None):
        """ Check for entity's requirements. """
        cls = other_cls or cls
        if cls is Entity:
            return all(sc.check() for sc in Entity._subclasses)
        cls._enabled, errors = True, {}
        # check for requirements using an explicitely defined function
        try:
            cls._enabled = cls.check_requirements(cls)
            # unpack requirement messages dictionary if relevant
            cls._enabled, err = cls._enabled
            errors.update(err or {})
        except (AttributeError, TypeError, ValueError):
            pass
        # for handling a NOT operator with an input item
        def _checkv(func, args, not_):
            r = func(*args) if isinstance(args, tuple) else func(args)
            return not_ ^ r
        # for unpacking a NOT operator from an input item
        def _unpackv(item):
            not_ = False
            # handle a NOT operator for the given item
            if item.startswith("!"):
                not_ = True
                item = item[1:]
            return not_, item
        # if 'value' is a function, execute it
        def _execv(value):
            if is_function(value):
                value = value(cls)
            return value
        # check requirements based on different criteria
        for k, v in getattr(cls, "requirements", {}).items():
            if is_function(v) and k != "internal":
                v = v(cls)
            if is_str(v):
                v = [v]
            # checks if a config option is set to a particular value
            if k == "config":
                if not is_dict(v):
                    raise ValueError("Bad config requirements (should be a dictionary)")
                for opt, exp_val in v.items():
                    cur_val = None
                    not_, opt = _unpackv(opt)
                    try:
                        cur_val = cls.config.option(opt.upper()).value
                    except KeyError:
                        pass
                    # compare current and expected values
                    ev = _execv(exp_val)
                    if not _checkv(lambda v1, v2: v1 is v2 or v1 == v2, (cur_val, ev), not_):
                        errors.setdefault('config', [])
                        errors['config'].append((opt, ev, not_))
                        cls._enabled = False
            # checks if a file exists
            elif k == "file":
                if not is_list(v):
                    raise ValueError("Bad file requirements (should be a list/set/tuple)")
                for fpath in v:
                    not_, fpath = _unpackv(fpath)
                    if not _checkv(lambda p: Path(cls.__file__).parent.joinpath(p).exists(), fpath, not_):
                        errors.setdefault('file', [])
                        errors['file'].append((fpath, not_))
                        cls._enabled = False
            # checks if a requirement wrt the console is met
            elif k == "internal":
                if not is_function(v):
                    raise ValueError("Bad internal requirement (should be a function)")
                if not v(cls):
                    cls._enabled = False
            # checks if a Python package is present
            elif k == "python":
                if not is_list(v):
                    raise ValueError("Bad python requirements (should be a list/set/tuple)")
                for module in v:
                    if isinstance(module, tuple):
                        module, package = module
                        not_, module = _unpackv(module)
                        found = find_spec(module, package)
                    else:
                        not_, module = _unpackv(module)
                        package = module
                        found = find_spec(module)
                    if not _checkv(lambda _: found is not None, "", not_):
                        errors.setdefault('python', [])
                        errors['python'].append((package, not_))
                        cls._enabled = False
            # checks if a state variable is set to a particular value
            elif k == "state":
                if is_list(v):
                    skeys = {sk: None for sk in v}
                elif is_dict(v):
                    skeys = v
                else:
                    raise ValueError("Bad state requirements (should be a list/set/tuple or a dictionary)")
                # catch Console from Entity's registered subclasses as Console cannot be imported in this module (cfr
                #  circular import)
                Console = cls.get_class("Console")
                _tmp = []
                # e.g. sk=INTERFACES and sv={None:[True,None,None]}
                for sk, sv in skeys.items():
                    # check if the state key exists
                    if sk not in Console._state.keys():
                        _tmp.append(sk)
                    # check if the value (if defined) matches
                    elif sv is not None:
                        # e.g. cs={wlp4s0:[False,None,"[MAC_addr]"]}
                        cs = Console._state[sk]
                        # special case: state value is a dict
                        if is_dict(sv) and is_dict(cs):
                            check_key, l = True, list(sv.items())
                            if len(l) == 1 and l[0][0] is None:
                                check_key = False
                            # case 1: classical dict
                            if check_key:
                                for ssk, ssv in sv.items():
                                    if ssk not in cs.keys() or cs[ssk] != ssv:
                                        _tmp.append(f"{sk}={sv}")
                                        break
                            # case 2: {None: ...}
                            else:
                                # e.g. ssv=[True,None,None]
                                ssv = l[0][1]
                                if isinstance(ssv, (tuple, list)):
                                    # e.g. this zips [True,None,None] and [False,None,"[MAC_addr]"] together
                                    found = False
                                    for values in zip(ssv, *list(cs.values())):
                                        ref = values[0]
                                        # None positional values are ignored
                                        if ref is not None and ref in values[1:]:
                                            found = True
                                    if not found:
                                        _tmp.append(f"{sk}?{ref}")
                                elif is_dict(ssv):
                                    # e.g. {monitor:True}
                                    found = False
                                    for sssk, sssv in ssv.items():
                                        for csd in cs.values():
                                            if sssv is None:
                                                if sssk in csd.keys():
                                                    found = True
                                                    break
                                            elif csd.get(sssk) == sssv:
                                                found = True
                                                break
                                        if not found:
                                            v = [f"{sssk}:{sssv}", sssv][sssv is None]
                                            _tmp.append(f"{sk}?{v}")
                                elif ssv not in cs.values():
                                    _tmp.append(f"{sk}?{ssv}")
                                    break
                        # exact match between any other type than dict
                        else:
                            if sv != Console._state[sk]:
                                _tmp.append(f"{sk}={sv}")
                if len(_tmp) > 0:
                    errors.setdefault("state", [])
                    errors['state'].extend(_tmp)
                    cls._enabled = False
            # checks if a system package/binary is installed
            elif k == "system":
                for tool in v:
                    tool = _execv(tool)
                    t = tool.split("/")
                    if len(t) == 1:
                        package = None
                        not_, tool = _unpackv(tool)
                    elif len(t) == 2:
                        package, tool = t
                        not_, package = _unpackv(package)
                    else:
                        raise ValueError("Bad system requirements (should be a list)")
                    if which(tool) is None:
                        if package is None:
                            errors.setdefault("tools", [])
                            errors["tools"].append((tool, not_))
                        else:
                            errors.setdefault("packages", [])
                            errors["packages"].append((package, not_))
                        cls._enabled = False
            else:
                raise ValueError(f"Unknown requirements type '{k}'")
        cls._errors = errors
        # check for applicability
        cls._applicable = True
        applies_to = getattr(cls, "applies_to", [])
        if len(applies_to) > 0:
            cls._applicable = False
            chk = getattr(cls, "check_applicability", None)
            if chk is not None:
                cls._applicable = cls.check_applicability()
            else:
                # format: ("attr1", "attr2", ..., "attrN", "value")
                #   e.g.: ("module", "fullpath", "my/module/do_something")
                for l in applies_to:
                    l, must_match, value = list(l[:-1]), l[-1], cls
                    while len(l) > 0:
                        value = getattr(value, l.pop(0), None)
                    if value and value == must_match:
                        cls._applicable = True
                        break
        return cls._enabled and cls._applicable
    
    @classmethod
    def get_class(cls, name):
        """ Get a class (key) from _subclasses by name (useful when the class is not imported in the current scope). """
        return Entity._subclasses[name]
    
    @classmethod
    def get_info(cls, *fields, show_all=False):
        """ Display entity's metadata and other information.
        
        :param fields:   metadata fields to be output
        :param show_all: also include unselected fields, to be output behind the list of selected fields
        """
        t = ""
        if len(fields) == 0:
            fields = [("name", "description"), ("author", "email", "version", "comments"), ("options",)]
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
        t = BorderlessTable(data, header=False).table + "\n" if len(data) > 0 else ""
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
            # try to unpack item for handling the NOT operator
            try:
                item, not_ = item
            except ValueError:
                not_ = False
            not_s = ["not ", ""][not_]
            subcls = Entity.get_subclass(None, scname)
            m = getattr(subcls, "requirements_messages", {}).get(key, {}).get(re.split(r"(\=|\?)", item, 1)[0])
            if m is not None:
                return m.format(item)
            if key == "file":
                return f"'{item}' {not_s}found"
            elif key == "packages":
                return f"'{item}' system package is {not_s}installed"
            elif key == "python":
                return f"'{item}' Python package is {not_s}installed"
            elif key == "tools":
                return f"'{item}' tool is {not_s}installed"
            elif key == "state":
                item = re.split(r"(\=|\?)", item, 1)
                if len(item) == 1:
                    return f"'{item[0]}' state key is not defined"
                elif item[1] == "=":
                    return f"'{item[0]}' state key does not match the expected value '{item[2]}'"
                elif item[1] == "?":
                    return f"'{item[0]}' state key is expected to have value '{item[2]}' at least once"
        # list issues using the related class method
        t = "\n"
        d = OrderedDict()
        # this regroups class names for error dictionaries that are the same in order to aggregate issues
        for cname, scname, errors in Entity.issues(subcls_name, category):
            e = str(errors)
            d.setdefault(e, {})
            d[e].setdefault(cname, [])
            d[e][cname].append(scname)
        # this then displays the issues with their list of related entities having these same issues
        for _, names in d.items():
            errors = list(Entity.issues(list(names.values())[0][0]))[0][-1]
            t = ""
            for cname, scnames in names.items():
                scnames = list(set(scnames))
                cname += ["", "s"][len(scnames) > 1]
                t += f"{cname}: {', '.join(sorted(scnames))}\n"
            # exception to issue messages: 'config' requirement
            t += "- " + "\n- ".join(msg(scname, k, e) for k, err in errors.items() for e in err if k != "config") + "\n"
        return "" if t.strip() == "" else t
    
    @classmethod
    def get_subclass(cls, key, name):
        """ Get a subclass (value) from _subclasses by name (useful when the related class is not imported in the
             current scope). """
        return Entity._subclasses[key, name]
    
    @classmethod
    def has_issues(cls, subcls_name=None, category=None):
        """ Tell if issues were encountered while checking entities. """
        for _ in cls.issues(subcls_name, category):
            return True
        return False
    
    @classmethod
    def issues(cls, subcls_name=None, category=None):
        """ List issues encountered while checking all the entities. """
        cls.check()
        sc = Entity._subclasses
        for c, l in sc.items() if cls is Entity else [cls, cls.subclasses] if cls in sc.keys() \
                                                else [(cls._entity_class, [cls])]:
            for subcls in l:
                e = {}
                for b in subcls.__bases__:
                    # do not consider base classes without the issues method (e.g. mixin classes)
                    if not hasattr(b, "issues"):
                        continue
                    # break when at parent entity level
                    if b in Entity._subclasses.keys() or b is Entity:
                        break
                    # update the errors dictionary starting with proxy classes
                    for _, __, errors in b.issues(category=category):
                        for categ, i in errors.items():
                            e.setdefault(categ, [])
                            e[categ].extend(i)
                # now update the errors dictionary of the selected subclass
                if hasattr(subcls, "_errors") and len(subcls._errors) > 0:
                    for categ, i in subcls._errors.items():
                        if category in [None, categ]:
                            e.setdefault(categ, [])
                            e[categ].extend(i)
                if len(e) > 0:
                    for categ, i in e.items():  # [categ]ory, [i]ssues
                        e[categ] = list(sorted(set(i)))
                    n = subcls.__name__
                    if subcls_name in [None, n]:
                        yield c.__name__, n, e
    
    @classmethod
    def register_subclass(cls, subcls):
        """ Maintain a registry of subclasses inheriting from Entity. """
        # get the base entity class
        ecls = subcls._entity_class
        Entity._subclasses.setdefault(ecls, [])
        if subcls not in Entity._subclasses[ecls]:
            # now register the subcls, ensured to be an end-subclass of the entity
            Entity._subclasses[ecls].append(subcls)
            # back-reference the entity from its config if existing
            if getattr(cls, "_has_config", False):
                setattr(subcls.config, "_" + subcls.entity, lambda: subcls._instance)
            # manually get subclass' name because of MetaModel not having the "name" property (would be considered a
            #  Peewee database field)
            n = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', subcls.__name__)).lower()
            logger.detail(f"Registered {subcls.entity} '{n}'")
    
    @classmethod
    def unregister_subclass(cls, subcls):
        """ Remove an entry from the registry of subclasses. """
        # manually get subclass' name because of MetaModel not having the "name" property (would be considered a Peewee
        #  database field)
        n = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', subcls.__name__)).lower()
        if cls in Entity._subclasses.keys():
            try:
                Entity._subclasses[cls].remove(subcls)
                logger.detail(f"Unregistered {subcls.entity} '{n}'")
            except ValueError:
                pass
    
    @classmethod
    def unregister_subclasses(cls, *subclss):
        """ Remove entries from the registry of subclasses. """
        for subcls in subclss:
            cls.unregister_subclass(subcls)
    
    def run(self, *args, **kwargs):
        """ Generic method for running Entity's logic. """
        raise NotImplementedError(f"{self.__class__.__name__}'s run() method is not implemented")


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
            try:
                subcls._entity_class = [c for c in mro_bases if c.__name__ in ENTITIES][0]
            except IndexError:
                return subcls
            # trigger class registration
            for b in bases:
                if not hasattr(subcls, "registered") or not subcls.registered:
                    b.register_subclass(subcls)
                    try:  # OPTIONAL: execute entity's own register method
                        getattr(b, "register_" + subcls.entity)(subcls)
                    except AttributeError:
                        pass
        return subcls
    
    def __repr__(self):
        return "<%s: %s>" % (self.entity.capitalize(), self.__name__)
    
    @property
    def entity(self):
        """ Normalized base entity name. """
        try:
            return self._entity_class.__name__.lower()
        except AttributeError:
            return "entity"
    
    @property
    def identifier(self):
        """ Compute a unique identifier for this entity subclass. """
        f = Path(getattr(self, "__file__", getfile(self)))
        d, fn = f.dirname, f.filename
        if len(d.parts) > 0 and d.parts[-1] == "__pycache__":
            parts = fn.split(".")
            if re.match(r".?python\-?[23]\d", parts[-2]):
                parts.pop(-2)
            parts[-1] = "py"
            f = d.parent.joinpath(".".join(parts))
        return str(f), self.__name__
    
    @property
    def registered(self):
        """ Boolean indicating if the entity is already registered. """
        e = self._entity_class
        Entity._subclasses.setdefault(e, [])
        return self.identifier in [x.identifier for x in Entity._subclasses[e]]
    
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
                    merge_dict(r, getattr(b, name, {}))
            merge_dict(r, self.__dict__.get(name, {}))
            return r
        return super(MetaEntity, self).__getattribute__(name)
    
    @property
    def applicable(self):
        """ Boolean indicating if the entity is applicable to the current context (i.e. of attached entities). """
        self.check()
        return self._applicable
    
    @property
    def enabled(self):
        """ Boolean indicating if the entity is enabled (i.e. if it has no missing requirement. """
        self.check()
        return self._enabled
    
    @property
    def name(self):
        """ Normalized entity subclass name. """
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', self.__name__)).lower()
    
    @property
    def options(self):
        """ Table of entity options. """
        if hasattr(self, "config") and isinstance(self.config, Config):
            data = [["Name", "Value", "Required", "Description"]]
            for n, d, v, r in sorted(self.config.items(), key=lambda x: x[0]):
                if v is None or n == v:
                    data.append([n, v, ["N", "Y"][r], d])
            return data


# -*- coding: UTF-8 -*-
from inspect import getfile
from tinyscript.helpers import flatten_dict, BorderlessTable, Path, PathBasedDict

from .components.logger import get_logger
from .entity import Entity, MetaEntity


__all__ = ["Module"]


logger = get_logger("core.module")


class MetaModule(MetaEntity):
    """ Metaclass of a Module. """
    _has_config       = True
    _inherit_metadata = True
    
    def __new__(meta, name, bases, clsdict):
        subcls = type.__new__(meta, name, bases, clsdict)
        # compute module's path from its root folder if no path attribute defined on its class
        if getattr(subcls, "path", None) is None:
            p = Path(getfile(subcls)).parent
            # collect the source temporary attribute
            s = getattr(subcls, "_source", ".")
            try:
                scp = p.relative_to(Path(s))
                if len(scp.parts) > 0 and scp.parts[-1] == "__pycache__":
                    scp = scp.parent
                subcls.path = str(scp)
            except ValueError:
                subcls.path = None
        # then pass the subclass with its freshly computed path attribute to the original __new__ method, for
        #  registration in subclasses and in the list of modules
        super(MetaModule, meta).__new__(meta, name, bases, clsdict, subcls)
        return subcls

    @property
    def base(self):
        """ Module's category. """
        return str(Path(self.fullpath).child) if self.category != "" else self.name
    
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
        """ Help message for the module. """
        return self.get_info(("name", "description"), "comments")
    
    @property
    def subpath(self):
        """ First child path of the module. """
        return str(Path(self.path).child)
    
    def search(self, text):
        """ Search for text in module's attributes. """
        t = text.lower()
        return any(t in "".join(v).lower() for v in self._metadata.values()) or t in self.fullpath


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
        """ Count the number of modules under the given path and matching attributes. """
        return cls.modules.count(path, **attrs)
    
    @classmethod
    def get_help(cls, category=None):
        """ Display command's help, using its metaclass' properties. """
        uncat = {}
        for c, v in cls.modules.items():
            if not isinstance(v, dict):
                uncat[c] = v
        if category is None:
            categories = list(set(cls.modules.keys()) - set(uncat.keys()))
            if len(uncat) > 0:
                categories += ["uncategorized"]
        else:
            categories = [category]
        s, i = "", 0
        for c in categories:
            d = [["Name", "Path", "Enabled", "Description"]]
            for n, m in sorted((flatten_dict(cls.modules.get(c, {})) if c != "uncategorized" else uncat).items(),
                               key=lambda x: x[1].name):
                e = ["N", "Y"][m.enabled]
                d.append([m.name, m.subpath, e, m.description])
            t = BorderlessTable(d, f"{c.capitalize()} modules")
            s += t.table + "\n\n"
            i += 1
        return "\n" + s.strip() + "\n" if i > 0 else ""
    
    @classmethod
    def get_list(cls):
        """ Get the list of modules' fullpath. """
        return sorted([m.fullpath for m in Module.subclasses if m.check()])
    
    @classmethod
    def get_modules(cls, path=None):
        """ Get the subdictionary of modules matching the given path. """
        return cls.modules[path or ""]
    
    @classmethod
    def get_summary(cls):
        """ Get the summary of module counts per category. """
        # display module stats
        m = []
        uncat = []
        for category in cls.modules.keys():
            if isinstance(cls.modules[category], MetaModule):
                uncat.append(cls.modules[category])
                continue
            l = "%d %s" % (Module.get_count(category), category)
            disabled = Module.get_count(category, enabled=False)
            if disabled > 0:
                l += " (%d disabled)" % disabled
            m.append(l)
        if len(uncat) > 0:
            l = "%d uncategorized" % len(uncat)
            disabled = len([u for u in uncat if not u.enabled])
            if disabled > 0:
                l += " (%d disabled)" % disabled
            m.append(l)
        if len(m) > 0:
            mlen = max(map(len, m))
            s = "\n"
            for line in m:
                s += f"\t-=[ {line: <{mlen}} ]=-\n"
            return s
        return ""
    
    @classmethod
    def register_module(cls, subcls):
        """ Register a Module subclass to the dictionary of modules. """
        if subcls.path is None:
            return  # do not consider orphan modules
        cls.modules[subcls.path, subcls.name] = subcls
    
    @classmethod
    def unregister_module(cls, subcls):
        """ Unregister a Module subclass from the dictionary of modules. """
        p, n = subcls.path, subcls.name
        try:
            del cls.modules[n if p == "." else (p, n)]
        except KeyError:
            pass
        for M in Module.subclasses:
            if p == M.path and n == M.name:
                Module.subclasses.remove(M)
                break
        logger.detail(f"Unregistered module '{p}/{n}'")
    
    @classmethod
    def unregister_modules(cls, *subcls):
        """ Unregister Module subclasses from the dictionary of modules. """
        for sc in subcls:
            cls.unregister_module(sc)
    
    def _feedback(self, success, failmsg):
        """ Dummy feedback method using a fail-message formatted with the "not" keyword (to be replaced by a null string
             in case of success). """
        if success is None:
            return
        elif success:
            self.logger.success(failmsg.replace("not ", ""))
        else:
            self.logger.failure(failmsg)


# -*- coding: UTF-8 -*-
import re
from termcolor import colored

from ...utils.objects import BorderlessTable
from ...utils.path import Path


__all__ = ["Config", "Option", "ProxyConfig", "ROption"]


class Config(dict):
    """ Enhanced dictionary for handling Option instances as its keys. """
    prefix = "Console"
    
    def __init__(self, *args, **kwargs):
        self.__d = {}
        # this will set options for this config, that is, creating NEW Option
        #  instances based on the given ones
        self.update(*args, **kwargs)
    
    def __add__(self, config):
        """ Method for appending another config. """
        return ProxyConfig() + self + config
    
    def __delitem__(self, key):
        """ Custom method for deleting an item, for triggering an unset callback
             from an Option. """
        key = self.__getkey(key)
        self.__run_callback(key, "unset")
    
    def __getitem__(self, key):
        """ Custom method for getting an item, returning the original value from
             the current Config instance or, if the key does not exist and this
             instance has a parent, try to get it from the parent. """
        try:  # search first in the private dictionary
            return self._getitem(key)
        except KeyError:
            pass
        try:  # then search in the parent ProxyConfig
            return self.parent[key]
        except (AttributeError, KeyError):
            pass
        try:  # finally search in the config of the parent console
            return self.console.parent.config[key]
        except (AttributeError, KeyError):
            pass
        raise KeyError(key)
    
    def __setitem__(self, key, value):
        """ Custom method for setting an item, keeping the original value in a
             private dictionary. """
        key = tmp = self.__getkey(key)
        # get an existing instance or the new one
        key = key.bind(self if not hasattr(key, "config") else key.config)
        if tmp is not key:
            del tmp  # if an instance already existed, remove the new one
        # keep track of the previous value
        key.old_value = self.__d.get(key.name)
        # then assign the new one if it is valid
        self.__d[key.name] = (key, value)
        if value and not key.validate(value):
            raise ValueError("Invalid value '{}'".format(value))
        super(Config, self).__setitem__(key, value)
        # when the value is validated and assigned, run the callback function
        self.__run_callback(key, "set")
        if key._reset:
            try:
                self.console.reset()
            except AttributeError:
                pass
    
    def __str__(self):
        """ Custom string method. """
        data = [["Name", "Value", "Required", "Description"]]
        for n, d, v, r in sorted(self.items(False), key=lambda x: x[0]):
            r = ["N", "Y"][r]
            if v == "":
                n, v, r = map(lambda s: colored(s, "red", attrs=['bold']),
                              [n, v, r])
            data.append([n, v, r, d])
        if len(data) > 1:
            s = ["", "s"][len(data) > 2]
            t = BorderlessTable(data, "{} option{}".format(self.prefix, s))
            return t.table
        return ""
    
    def __getkey(self, key):
        """ Proxy method for ensuring that the key is an Option instance. """
        if not isinstance(key, Option):
            if not isinstance(key, tuple):
                key = (key,)
            key = Option(*key)
        return key
    
    def __run_callback(self, key, name):
        """ Method for executing a callback and updating the current value with
             its return value if any. """
        retval = None
        if hasattr(self, "_last_error"):
            del self._last_error
        try:
            retval = getattr(key, "{}_callback".format(name))()
        except Exception as e:
            self._last_error = e
        if retval is not None:
            key.old_value = key.value
            if not key.validate(retval):
                raise ValueError("Invalid value '{}'".format(retval))
            self.__d[key.name] = (key, retval)
    
    def _getitem(self, key):
        """ Custom method for getting an item, returning the original value from
             the current Config instance. """
        if isinstance(key, Option):
            key = key.name
        return self.__d[key][1]
    
    def _getoption(self, key):
        """ Return Option instance from key. """
        if isinstance(key, Option):
            key = key.name
        return self.__d[key][0]
    
    def copy(self, config, key):
        """ Copy an option based on its key from another Config instance. """
        self[config.option(key)] = config[key]
    
    def items(self, fail=True):
        """ Return (key, descr, value, required) instead of (key, value). """
        for o in sorted(self, key=lambda x: x.name):
            try:
                n = str(o.name)
                v = o.value
            except ValueError as e:
                if fail:
                    raise e
                v = ""
            yield n, o.description or "", v, o.required
    
    def keys(self):
        """ Return string keys (like original dict). """
        for k in sorted(self.__d.keys()):
            yield k
    
    def option(self, key):
        """ Return Option instance from key. """
        try:  # search first in the private dictionary
            return self._getoption(key)
        except KeyError:
            pass
        try:  # then search in the parent ProxyConfig
            return self.parent.option(key)
        except (AttributeError, KeyError):
            pass
        try:  # finally search in the config of the parent console
            return self.console.parent.config.option(key)
        except (AttributeError, KeyError):
            pass
        raise KeyError(key)
    
    def options(self):
        """ Return Option instances instead of keys. """
        for k in sorted(self.__d.keys()):
            yield self.__d[k][0]
    
    def setdefault(self, key, value=None):
        """ Custom method for forcing the use of the modified __setitem__. """
        if key not in self:
            self[key] = value
        return self[key]
    
    def update(self, *args, **kwargs):
        """ Custom update method for handling update of another Config and
             forcing the use of the modified __setitem__. """
        if len(args) > 0:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, got %d" \
                                % len(args))
            d = args[0]
            for k in (d.options() if isinstance(d, Config) else \
                      d.keys() if isinstance(d, dict) else []):
                self[k] = d[k]
        # important note: this way, this will cause Option instances to be bound
        #                  to THIS Config instance, with their default attribute
        #                  values (description, required, ...)
        for k, v in kwargs.items():
            self[k] = v
    
    @property
    def bound(self):
        return hasattr(self, "_console") or \
               (hasattr(self, "module") and hasattr(self.module, "console"))
    
    @property
    def console(self):
        # check first that the console is back-referenced on an attached module
        #  instance
        if hasattr(self, "module") and hasattr(self.module, "console"):
            return self.module.console
        # then check for a direct reference
        if self.bound:
            c = self._console
            return c() if isinstance(c, type(lambda:0)) else c
        # finally try to get it from the parent ProxyConfig
        if hasattr(self, "parent"):
            # reference the callee to let ProxyConfig.__getattribute__ avoid
            #  trying to get the console attribute from the current config
            #  object, ending in an infinite loop
            self.parent._caller = self
            try:
                return self.parent.console
            except AttributeError:
                pass
        raise AttributeError("'Config' object has no attribute 'console'")
    
    @console.setter
    def console(self, value):
        self._console = value


class Option(object):
    """ Class for handling an option with its parameters while using it as key
         for a Config dictionary. """
    _instances = {}
    _reset     = False
    old_value  = None
    
    def __init__(self, name, description=None, required=False, choices=None,
                 set_callback=None, unset_callback=None,
                 transform=None, validate=None):
        self.name = name
        self.description = description
        self.required = required
        if choices is bool:
            choices = ["true", "false"]
        self._choices = choices
        self.__set_func(transform, "transform")
        if validate is None and choices is not None:
            validate = lambda s, v: str(v).lower() in \
                                    [str(_).lower() for _ in s.choices]
        self.__set_func(validate, "validate")
        self.__set_func(set_callback, "set_callback", lambda *a, **kw: None)
        self.__set_func(unset_callback, "unset_callback", lambda *a, **kw: None)
    
    def __repr__(self):
        """ Custom representation method. """
        return str(self)
    
    def __str__(self):
        """ Custom string method. """
        return "<{}[{}]>".format(self.name, ["N", "Y"][self.required])
    
    def __set_func(self, func, name, default_func=None):
        """ Set a function, e.g. for manipulating option's value. """
        if func is None:
            func = default_func or \
                   (lambda *a, **kw: a[-1] if len(a) > 0 else None)
        if isinstance(func, type(lambda:0)):
            setattr(self, name, func.__get__(self, self.__class__))
        else:
            raise Exception("Bad {} lambda".format(name))
    
    def bind(self, parent):
        """ Register this instance as a key of the given Config or retrieve the
             already existing one. """
        o, i = Option._instances, id(parent)
        o.setdefault(i, {})
        if o[i].get(self.name) is None:
            self.config = parent
            o[i][self.name] = self
        else:
            o[i][self.name].config = parent
        return o[i][self.name]
    
    @property
    def choices(self):
        """ Pre- or lazy-computed list of choices. """
        c = self._choices
        if not isinstance(c, type(lambda:0)):
            return c
        try:
            return c()
        except TypeError:
            return c(self)

    @property
    def console(self):
        """ Shortcut to parent config's console attribute. """
        return self.config.console
    
    @property
    def input(self):
        """ Original input value. """
        if hasattr(self, "config"):
            return self.config[self]
        else:
            raise Exception("Unbound option {}".format(self.name))

    @property
    def module(self):
        """ Shortcut to parent config's console bound module attribute. """
        return self.console.module

    @property
    def root(self):
        """ Shortcut to parent config's root console attribute. """
        return self.console.root

    @property
    def state(self):
        """ Shortcut to parent console's state attribute. """
        return self.console.state
    
    @property
    def value(self):
        """ Normalized value attribute. """
        value = self.input
        if self.required and value is None:
            raise ValueError("{} must be defined".format(self.name))
        try:
            # try to expand format variables using console's attributes
            kw = {}
            for n in re.findall(r'\{([a-z]+)\}', str(value)):
                kw[n] = self.config.console.__dict__.get(n, "")
            try:
                value = value.format(**kw)
            except:
                pass
        except AttributeError as e:  # occurs when console is not linked to
            pass                     #  config (i.e. at startup)
        # expand and resolve paths
        if self.name.endswith("FOLDER") or self.name.endswith("WORKSPACE"):
            # this will ensure that every path is expanded
            value = str(Path(value, expand=True))
        # convert common formats to their basic types
        try:
            if value.isdigit():
                value = int(value)
            if value.lower() in ["false", "true"]:
                value = value.lower() == "true"
        except AttributeError:  # occurs e.g. if value is already a bool
            pass
        # then try to transform using the user-defined function
        if isinstance(self.transform, type(lambda:0)) and \
            self.transform.__name__ == (lambda:0).__name__:
            value = self.transform(value)
        return value


class ProxyConfig(object):
    """ Proxy class for mixing multiple Config instances, keeping original
         references to Option instances (as they are managed based on
         Config's instance identifier). """
    def __init__(self, *args):
        self.__configs = []
        for config in args:
            self.append(config)
    
    def __add__(self, config):
        """ Method for appending another config. """
        self.append(config)
        return self
    
    def __getattribute__(self, name):
        """ Custom getattribute method for aggregating Config instances for some
             specific methods and attributes. """
        # try to get it from this class first
        try:
            return super(ProxyConfig, self).__getattribute__(name)
        except AttributeError:
            pass
        # for these methods, create an aggregated config and get its attribute
        #  from this new instance
        if name in ["items", "keys", "options"]:
            try:
                c = Config()
                for config in self.__configs:
                    c.update(config)
            except IndexError:
                c = Config()
            return c.__getattribute__(name)
        # for this attribute, only try to get this of the first config
        if name == "console":
            c = self.__configs[0]
            if c is not getattr(self, "_caller", None):
                if c.bound:
                    return c.console
        # for any other, get the first one found from the list of configs
        else:
            for c in self.__configs:
                if name != "_caller" and c is getattr(self, "_caller", None):
                    continue
                try:
                    return c.__getattribute__(name)
                except AttributeError:
                    continue
        raise AttributeError("'ProxyConfig' object has no attribute '{}'"
                             .format(name))
    
    def __getitem__(self, key):
        """ Get method for returning the first occurrence of a key among the
             list of Config instances. """
        # search for the first config that has this key and return the value
        for c in self.configs:
            try:
                return c._getitem(key)
            except KeyError:
                pass
        # if not found, raise KeyError
        raise KeyError(key)
    
    def __setattr__(self, name, value):
        """ Custom setattr method for handling the backref to a console. """
        if name == "console":
            if len(self.configs) > 0:
                self.configs[0].console = value
        else:
            super(ProxyConfig, self).__setattr__(name, value)
    
    def __setitem__(self, key, value):
        """ Set method setting a key-value pair in the right Config among the
             list of Config instances. First, it tries to get the option
             corresponding to the given key and if it exists, it sets the value.
             Otherwise, it sets a new key in the first Config among the list """
        try:
            c = self.option(key).config
        except KeyError:
            c = self.configs[0] if len(self.configs) > 0 else Config()
        return c.__setitem__(key, value)
    
    def __str__(self):
        """ String method for aggregating the list of Config instances. """
        c = Config()
        for config in self.configs:
            c.update(config)
        return str(c)
    
    def append(self, config):
        """ Method for apending a config to the list (if it does not exist). """
        for c in ([config] if isinstance(config, Config) else config.configs):
            if c not in self.configs:
                self.configs.append(c)
                c.parent = self
    
    def get(self, key, default=None):
        """ Adapted get method (wrt Config). """
        try:
            return self[key]
        except KeyError:
            return default
    
    def option(self, key):
        """ Adapted optoin method (wrt Config). """
        # search for the first config that has this key and return its Option
        for c in self.configs:
            try:
                self[key]
                return c._getoption(key)
            except KeyError:
                pass
        # if not found, raise KeyError
        raise KeyError(key)
    
    @property
    def configs(self):
        return self.__configs


class ROption(Option):
    """ Class for handling a reset option (that is, an option that triggers a
         console reset after change) with its parameters while using it as key
         for a Config dictionary. """
    _reset = True

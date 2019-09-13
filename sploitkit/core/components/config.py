# -*- coding: UTF-8 -*-
import re
from copy import copy
from itertools import chain

from ...utils.path import Path


__all__ = ["Config", "Option", "ProxyConfig"]


class Config(dict):
    """ Enhanced dictionary for handling Option instances as its keys. """
    bind = True  # class attribute used to bind a parent class to a Config
                 #  instance
    def __init__(self, *args, **kwargs):
        self.__d = {}
        # this will set options for this config, that is, creating NEW Option
        #  instances based on the given ones
        self.update(*args, **kwargs)
    
    def __add__(self, config):
        """ Method for appending another config. """
        return ProxyConfig() + self + config
    
    def __del__(self):
        """ Custom deletion method, for removing back-references. """
        if hasattr(self, "console"):
            delattr(self, "console")

    def __delitem__(self, key):
        """ Custom method for deleting an item, for triggering an unset callback
             from an Option. """
        key = self.__getkey(key)
        self.__run_callback(key, "unset")
    
    def __getitem__(self, key):
        """ Custom method for getting an item, returning the original value from
             the current Config instance or, if the key does not exist and this
             instance has a parent, try to get it from the parent. """
        if isinstance(key, Option):
            key = key.name
        try:
            return self.__d[key][1]
        except KeyError:
            if hasattr(self, "console") and self.console.parent is not None:
                return self.console.parent.config[key]
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
        key.old_value = key.value if self.__d.get(key.name) else None
        # then assign the new one
        self.__d[key.name] = (key, value)
        if not key.validate(value):
            raise ValueError("Invalid value '{}'".format(value))
        super(Config, self).__setitem__(key, value)
        # when the value is validated and assigned, run the callback function
        self.__run_callback(key, "set")
        if key._reset:
            if hasattr(self, "console"):
                self.console.reset()
    
    def __getkey(self, key):
        """ Proxy method for ensuring that the key is an Option instance. """
        if not isinstance(key, Option):
            if not isinstance(key, tuple):
                key = (key, )
            key = Option(*key)
        return key
    
    def __run_callback(self, key, name):
        """ Method for executing a callback and updating the current value with
             its return value if any. """
        retval = None
        try:
            retval = getattr(key, "{}_callback".format(name))()
        except Exception as e:
            self._last_error = str(e)
        if retval is not None:
            key.old_value = key.value
            if not key.validate(retval):
                raise ValueError("Invalid value '{}'".format(retval))
            self.__d[key.name] = (key, retval)
    
    def copy(self, config, key):
        """ Copy an option based on its key from another Config instance. """
        self[config.option(key)] = config[key]

    def items(self):
        """ Return (key, descr, value, required) instead of (key, value). """
        for o in sorted(self, key=lambda x: x.name):
            yield str(o.name), o.description or "", o.value, o.required

    def keys(self):
        """ Return string keys (like original dict). """
        for k in sorted(self.__d.keys()):
            yield k
    
    def option(self, key):
        """ Return Option instance from key. """
        if isinstance(key, Option):
            key = key.name
        try:
            return self.__d[key][0]
        except KeyError:
            if hasattr(self, "console") and self.console.parent is not None:
                return self.console.parent.config.option(key)
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
    
    def __del__(self):
        """ Custom deletion method, for removing back-references. """
        if hasattr(self, "console"):
            delattr(self, "console")
    
    def __repr__(self):
        """ Custom representation method. """
        return str(self)
    
    def __str__(self):
        """ Custom string method. """
        return "<{}[required={}]: {}>" \
               .format(self.name, self.required, self.value)
    
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
    
    def copy(self):
        """ Copy option information to a new Option instance. """
        return Option(self.name, self.description, self.required, self.choices, 
                      self.set_callback, self.unset_callback,
                      self.transform, self.validate)
    
    @property
    def choices(self):
        """ Pre- or lazy-computed list of choices. """
        c = self._choices
        return c() if isinstance(c, type(lambda:0)) else c
    
    @property
    def input(self):
        """ Original input value. """
        if hasattr(self, "config"):
            return self.config[self]
        else:
            raise Exception("Unbound option {}" .format(self.name))
    
    @property
    def value(self):
        """ Normalized value attribute. """
        value = self.input
        if self.required and value is None:
            raise ValueError("{} must be defined" .format(self.name))
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
    
    def __del__(self):
        """ Custom deletion method, for removing back-references. """
        try:
            super().__delattr__("console")
        except AttributeError:
            pass
    
    def __getattribute__(self, name):
        """ Custom getattribute method for aggregating Config instances for some
             specific methods and attributes. """
        # for these methods, create an aggregated config and get its attribute
        #  from this new instance
        if name in ["items", "keys", "options"]:
            try:
                c = Config()
                for config in self.configs:
                    c.update(config)
            except IndexError:
                c = Config()
            return c.__getattribute__(name)
        # for any other, try to get it from this class, otherwise get this of
        #  the first config in the list
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass
        for config in self.configs:
            try:
                return config.__getattribute__(name)
            except AttributeError:
                continue
        msg = "'ProxyConfig' object has no attribute '{}'".format(name)
        raise AttributeError(msg)
    
    def __getitem__(self, key):
        """ Get method for returning the first occurrence of a key among the
             list of Config instances. """
        # search for the first config that has this key and return the value
        for config in self.configs:
            try:
                return config[key]
            except KeyError:
                pass
        # if not found, raise KeyError
        raise KeyError(key)
    
    def __setattr__(self, name, value):
        """ Custom setattr method for handling the backref to a console. """
        if name == "console":
            for config in self.configs:
                if not hasattr(config, "console"):
                    config.console = value
        super().__setattr__(name, value)
    
    def __setitem__(self, key, value):
        """ Set method setting a key-value pair in the right Config among the
             list of Config instances. It first tries to get the option
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
            if c not in self.configs and len(c) > 0:
                self.configs.append(c)
    
    def get(self, key, default=None):
        """ Adapted get method (wrt Config). """
        try:
            return self[key]
        except KeyError:
            return default
    
    def option(self, key):
        """ Adapted optoin method (wrt Config). """
        # search for the first config that has this key and return its Option
        for config in self.configs:
            try:
                self[key]
                return config.option(key)
            except KeyError:
                pass
        # if not found, raise KeyError
        raise KeyError(key)
    
    @property
    def configs(self):
        """ List of configs. """
        return self.__configs

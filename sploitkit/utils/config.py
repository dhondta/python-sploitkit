from __future__ import unicode_literals


__all__ = ["Config", "Option"]


class Config(dict):
    """ Enhanced dictionary for handling Option instances as its keys. """
    def __init__(self, *args, **kwargs):
        self.__d = {}
        self.update(*args, **kwargs)
    
    def __getitem__(self, key):
        if isinstance(key, Option):
            key = key.name
        return self.__d[key]
    
    def __setitem__(self, key, value):
        if not isinstance(key, Option):
            key = Option(key)
        tmp = key
        key = key.bind(self)  # get an existing instance or the new one
        if tmp is not key: 
            del tmp  # if an instance already existed, remove the new one
        self.__d[key.name] = value
        super(Config, self).__setitem__(key, value)

    def items(self):
        """ Return (key, descr, value, required) instead of (key, value). """
        return [(str(o.name), o.description or "", str(o.value), o.required) \
                for o in sorted(self, key=lambda x: x.name)]

    def keys(self):
        """ Return string keys (like original dict). """
        return sorted(self.__d.keys())

    def option(self, key):
        """ Return Option instance from key. """
        return Option(key)

    def update(self, *args, **kwargs):
        """ Custom update method for handling update of another Config and
             forcing the use of the modified __setitem__. """
        if len(args) > 0:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, got %d" \
                                % len(args))
            d = args[0]
            for k in d:
                self[k] = d[k]
        for k, v in kwargs.items():
            self[k] = v

    def setdefault(self, key, value=None):
        """ Custom method for forcing the use of the modified __setitem__. """
        if key not in self:
            self[key] = value
        return self[key]


class Option(object):
    """ Class for handling an option with its parameters while using it as key
         for a Config dictionary. """
    _instances = {}
    
    def __init__(self, name, description=None, required=False):
        self.name = name
        self.description = description
        self.required = required
    
    def bind(self, parent):
        """ Register this instance as a key of the given Config or retrieve the
             already existing one. """
        o, i = Option._instances, id(parent)
        o.setdefault(i, {})
        if o[i].get(self.name) is None:
            self._config = parent
            o[i][self.name] = self
        else:
            o[i][self.name]._config = parent
        return o[i][self.name]
    
    @property
    def value(self):
        if hasattr(self, "_config"):
            _ = self._config[self]
            if self.required and _ is None:
                raise ValueError("{} must be defined" .format(self.name))
            else:
                return _ or ""

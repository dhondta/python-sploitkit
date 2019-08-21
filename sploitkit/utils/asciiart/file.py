# -*- coding: UTF-8 -*-
import re
from collections import OrderedDict
from random import choice
from terminaltables.terminal_io import terminal_size as termsize
try:
    import colorama
    _color_enabled = True
    COLORS = list(vars(colorama.Fore).values())
except ImportError:
    _color_enabled = False


__all__ = ["AsciiFile"]

DEFAULT_PARAMS = {'adjust': "center"}
SECTION_LINE = re.compile(r"^\.section\:\s(?P<section>[a-z0-9]+)(?:\[(?P"
                          r"<params>([a-z]+\=[a-z]+)(\,[a-z]+\=[a-z]+)*)\])?")

center = lambda t, w: "\n".join(l.center(w) for l in t.split("\n"))


class AsciiFile(object):
    """ ASCII art custom file format (with sections).
    
    This organizes ASCII art items as sections in a custom file format for
     applying different style parameters.
    
    :param path: path to the ASCII art file
    """
    def __init__(self, path=None):
        self.__sections = OrderedDict()
        self.__params = {}
        self.load(path)

    def __str__(self):
        t, color_changed = "", False
        for section, item, params in self.items():
            text = str(item)
            # apply parameters in the following order
            for param in ["adjust", "bgcolor", "fgcolor"]:
                value = params.get(param)
                if value is None:
                    continue
                if param in ["bgcolor", "fgcolor"] and _color_enabled:
                    _ = getattr(colorama, ["Fore", "Back"][param == "bgcolor"])
                    color = getattr(_, value.upper(), None)
                    if value == "random":
                        text = "".join(choice(COLORS) + c for c in text)
                    elif color is not None:
                        text = color + text
                    color_changed = True
                elif param == "adjust":
                    s = ""
                    if value in ["left", "right"]:
                        m = ["rjust", "ljust"][value == "left"]
                        for l in text.split("\n"):
                            s += getattr(l, m)(termsize()[0]) + "\n"
                    elif value == "center":
                        for l in text.split("\n"):
                            s += center(l, termsize()[0]) + "\n"
                    else:
                        raise ValueError("Bad adjustment parameter value")
                    text = s
            # then add the text to the final string
            t += text + "\n"
            if _color_enabled and color_changed:
                t += "\x1b[37m"
        return t[:-1]
    
    def __delitem__(self, name):
        del self.__sections[name]
        del self.__params[name]
    
    def __getitem__(self, name):
        return self.__sections[name], self.__params[name]
    
    def __setitem__(self, name, item):
        params = {}
        if isinstance(name, tuple):
            name, params = name
        if not isinstance(params, dict):
            raise ValueError("'{}' shall be a dictionary".format(params))
        params.update(DEFAULT_PARAMS)
        self.__sections[name] = item
        self.__params.setdefault(name, {})
        self.__params[name].update(params)
    
    def get(self, name, default=None):
        try:
            self[name]
        except KeyError:
            return default
    
    def items(self):
        for name, item in self.__sections.items():
            yield name, item, self.__params[name]
    
    def load(self, path=None):
        """ Load sections from a file """
        path = path or getattr(self, "path", None)
        self.path = str(path)
        if path is not None:
            with open(path) as f:
                _ = f.read()
            self.text = _
    
    def save(self, path=None):
        """ Save the current sections to a file """
        path = path or getattr(self, "path", None)
        self.path = str(path)
        if path is not None:
            path = path if path.endswith(".asc") else path + ".asc"
            with open(path, 'w') as f:
                for section, text in self.__sections.items():
                    p = ",".join("{}={}".format(k, v) for k, v in \
                                 self.__params[section].items() \
                                 if k not in DEFAULT_PARAMS.keys())
                    p = ["", "[{}]".format(p)][len(p) > 0]
                    f.write(".section: {}{}\n".format(section, p))
                    f.write(str(text) + "\n")
    
    @property
    def sections(self):
        return self.__sections.keys()
    
    @property
    def text(self):
        return str(self)
    
    @text.setter
    def text(self, text):
        """ Parse the input text into sections """
        self.__sections = s = OrderedDict()
        self.__params = p = {}
        section = "main"
        for l in text.split("\n"):
            s.setdefault(section, "")
            if l.startswith(".section: "):
                try:
                    _ = SECTION_LINE.search(l).groupdict()
                except AttributeError:
                    raise ValueError("Bad section line format")
                section = _["section"]
                params = {}
                for pair in (_["params"] or "").split(","):
                    if pair.strip() == "":
                        continue
                    name, value = pair.strip().split("=")
                    params[name.strip()] = value.strip()
                p[section] = params
            else:
                s[section] += l + "\n"
        s[section] = s[section][:-1]
        if s["main"] == "":
            del s["main"]

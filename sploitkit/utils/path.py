from __future__ import unicode_literals

import os
import random
import shutil
from os.path import expanduser
from pathlib import Path as BasePath
from pkgutil import ImpImporter
from pygments.lexers import PythonLexer


__all__ = ["Path", "PyFolderPath", "PyModulePath", "RandPath"]


lexer = PythonLexer()


class Path(BasePath):
    """ Extension of the base class Path from pathlib. """
    _flavour = BasePath()._flavour  # fix to AttributeError
    
    def __new__(cls, *args, **kwargs):
        if kwargs.pop("expand", False):
            _ = expanduser(str(BasePath(*args, **kwargs)))
            p = BasePath(_, **kwargs).resolve()
            if kwargs.pop("create", False):
                p.mkdir(parents=True, exist_ok=True)
            args = (str(p), )
        return super(Path, cls).__new__(cls, *args, **kwargs)
    
    @property
    def child(self):
        """ Get the child path relative to self's one. """
        return Path(*self.parts[1:])
    
    @property
    def size(self):
        """ Get path's size. """
        if self.is_file() or self.is_symlink():
            return self.stat().st_size
        elif self.is_dir():
            s = 0
            for f in self.glob("**/*"):
                s += os.stat(str(f)).st_size
            return s
    
    def append_bytes(self, text):
        """ Allows to append bytes to the file, as only write_bytes is available
             in pathlib, overwritting the former bytes at each write. """
        with open(str(self), 'ab') as f:
            f.write(text)
    
    def append_line(self, line):
        """ Shortcut for appending a single line (text with newline). """
        self.append_text(line + '\n')
    
    def append_lines(self, *lines):
        """ Shortcut for appending a bunch of lines. """
        for line in lines:
            self.append_line(line)
    
    def append_text(self, text):
        """ Allows to append text to the file, as only write_text is available
             in pathlib, overwritting the former text at each write. """
        with open(str(self), 'a') as f:
            f.write(text)
    
    def expanduser(self):
        """ Fixed expanduser() method, working for both Python 2 and 3. """
        return Path(expanduser(str(self)))
    
    def iterpubdir(self):
        """ List all public subdirectories from the current directory. """
        for i in self.iterdir():
            if i.is_dir() and not i.stem.startswith("."):
                yield i
    
    def iterfiles(self, filetype=None):
        """ List all files from the current directory. """
        for i in self.iterdir():
            if i.is_file():
                if filetype is None or i.suffix == filetype:
                    yield i
    
    def read_text(self):
        """ Fix to non-existing method in Python 2. """
        try:
            super(Path, self).read_text()
        except AttributeError:  # occurs with Python 2 ; no write_text method
            with open(str(self), 'r') as f:
                c = f.read()
            return c
    
    def reset(self):
        """ Ensure the file exists and is empty. """
        if self.exists():
            self.unlink()
        self.touch()
    
    def rmtree(self):
        """ Extension for recursively removing a directory. """
        shutil.rmtree(str(self))
    
    def samepath(self, otherpath):
        """ Check if both paths have the same parts. """
        return self.parts == otherpath.parts
    
    def write_text(self, text):
        """ Fix to non-existing method in Python 2. """
        try:
            super(Path, self).write_text(text)
        except AttributeError:  # occurs with Python 2 ; no write_text method
            with open(str(self), 'w+') as f:
                f.write(text)


class RandPath(Path):
    """ Extension for choosing a random file amongst the current folder. """
    def choice(self, filetype=None):
        """ Return a random file from the current directory. """
        try:
            return self.joinpath(random.choice(list(self.iterfiles(filetype))))
        except:
            return
    
    def generate(self, length=8, alphabet="0123456789abcdef"):
        """ Generate a random folder name. """
        return self.joinpath("".join(choice(alphabet) for i in range(length)))


class PyFolderPath(Path):
    """ Extension for handling a Python module and loading all subclasses of a
         given class from this module. """
    def __init__(self, path):
        super(PyFolderPath, self).__init__()
        self.modules = []
        if self.is_dir():
            for d in self.glob("**/*.py"):
                if d.is_file():
                    p = PyModulePath(d)
                    if p.is_pymodule:
                        self.modules.append(p.module)


class PyModulePath(Path):
    """ Extension for handling a Python module and loading all subclasses of a
         given class from this module. """
    def __init__(self, path):
        super(PyModulePath, self).__init__()
        self.is_pymodule = self.is_file() and \
                           lexer.analyse_text(self.open().read()) == 1.0
        if self.is_pymodule:
            self.module = ImpImporter(str(self.resolve().parent)) \
                          .find_module(self.stem).load_module(self.stem)

    def get_classes(self, *base_cls):
        """ Yield a list of all subclasses inheriting from the given class from
             the Python module. """
        if not self.is_pymodule:
            return
        for n in dir(self.module):
            cls = getattr(self.module, n)
            try:
                if issubclass(cls, base_cls) and cls not in base_cls:
                    yield cls
            except TypeError:
                pass

    def has_class(self, base_cls):
        """ Check if the Python module has the given class. """
        if not self.is_pymodule:
            return
        for n in dir(self.module):
            try:
                cls = getattr(self.module, n)
                if issubclass(cls, base_cls) and cls is not base_cls:
                    return True
            except TypeError:
                pass
        return False

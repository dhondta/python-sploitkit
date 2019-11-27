# -*- coding: UTF-8 -*-
import os
import random
import shutil
from os.path import expanduser
from pathlib import Path as BasePath
from pkgutil import ImpImporter
from pygments.lexers import Python2Lexer
from tempfile import gettempdir, NamedTemporaryFile as TempFile


__all__ = ["Path", "PyFolderPath", "PyModulePath", "TempPath"]


# NB: PythonLexer.analyse_text only relies on shebang !
lexer = Python2Lexer()


class Path(BasePath):
    """ Extension of the base class Path from pathlib. """
    _flavour = BasePath()._flavour  # fix to AttributeError
    
    def __new__(cls, *args, **kwargs):
        if kwargs.pop("expand", False):
            _ = expanduser(str(BasePath(*args, **kwargs)))
            p = BasePath(_, *args[1:], **kwargs).resolve()
            args = (str(p),) + args[1:]
        if kwargs.pop("create", False):
            BasePath(*args, **kwargs).mkdir(parents=True, exist_ok=True)
        return super(Path, cls).__new__(cls, *args, **kwargs)
    
    @property
    def child(self):
        """ Get the child path relative to self's one. """
        return Path(*self.parts[1:])
    
    @property
    def filename(self):
        """ Get the file name, without the complete path. """
        return self.stem + self.suffix
    
    @property
    def size(self):
        """ Get path's size. """
        if self.is_file() or self.is_symlink():
            return self.stat().st_size
        elif self.is_dir():
            s = 4096  # include the size of the directory itself
            for root, dirs, files in os.walk(str(self)):
                s += 4096 * len(dirs)
                for f in files:
                    s += os.stat(str(Path(root).joinpath(f))).st_size
            return s
        raise AttributeError("object 'Path' has no attribute 'size'")
    
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
    
    def choice(self, *filetypes):
        """ Return a random file from the current directory. """
        filetypes = list(filetypes)
        while len(filetypes) > 0:
            filetype = random.choice(filetypes)
            filetypes.remove(filetype)
            l = list(self.iterfiles(filetype, filename_only=True))
            try:
                return self.joinpath(random.choice(l))
            except:
                continue
    
    def expanduser(self):
        """ Fixed expanduser() method, working for both Python 2 and 3. """
        return Path(expanduser(str(self)))
    
    def generate(self, prefix="", suffix="", length=8,
                 alphabet="0123456789abcdef"):
        """ Generate a random folder name. """
        rname = "".join(random.choice(alphabet) for i in range(length))
        return self.joinpath(prefix + rname + suffix)
    
    def iterpubdir(self):
        """ List all public subdirectories from the current directory. """
        for i in self.iterdir():
            if i.is_dir() and not i.stem.startswith("."):
                yield i
    
    def iterfiles(self, filetype=None, filename_only=False, relative=False):
        """ List all files from the current directory. """
        for i in self.iterdir():
            if i.is_file():
                if filetype is None or i.suffix == filetype:
                    yield i.filename if filename_only else \
                          i.relative_to(self) if relative else i
    
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


class PyFolderPath(Path):
    """ Path extension for handling the dynamic import of every Python module
         inside the given folder. """
    def __init__(self, path):
        super(PyFolderPath, self).__init__()
        self.modules = []
        if self.is_dir():
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith(".py"):
                        p = PyModulePath(Path(root).joinpath(f))
                        if p.is_pymodule:
                            self.modules.append(p.module)


class PyModulePath(Path):
    """ Path extension for handling the dynamic import of a Python module. """
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


class TempPath(Path):
    """ Extension of the class Path for handling a temporary path.
    
    :param length:   length for the folder name (if 0, do not generate a folder
                      name, e.g. keeping /tmp)
    :param alphabet: character set to be used for generating the folder name
    """
    def __new__(cls, **kwargs):
        kw = {}
        kw["prefix"]   = kwargs.pop("prefix", "")
        kw["suffix"]   = kwargs.pop("suffix", "")
        kw["length"]   = kwargs.pop("length", 0)
        kw["alphabet"] = kwargs.pop("alphabet", "0123456789abcdef")
        _ = Path(gettempdir())
        kwargs["create"] = True   # force creation
        kwargs["expand"] = False  # expansion is not necessary
        if kw["length"] > 0:
            while True:
                # ensure this is a newly generated path
                tmp = _.generate(**kw)
                if not tmp.exists():
                    break
            return super(TempPath, cls).__new__(cls, tmp, **kwargs)
        return super(TempPath, cls).__new__(cls, _, **kwargs)
    
    def joinpath(self, *args):
        """ Modifed joinpath to return a Path instance instead of TempPath. """
        return Path(self).joinpath(*args)
    
    def tempfile(self, **kwargs):
        """ Create a NamedTemporaryFile in the TempPath. """
        kwargs.pop("dir", None)
        tf = TempFile(dir=str(self), **kwargs)
        tf.folder = self
        return tf

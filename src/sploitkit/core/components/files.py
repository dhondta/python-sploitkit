# -*- coding: UTF-8 -*-
import re
import requests
from ftplib import FTP, FTP_TLS
from shutil import which
from subprocess import call, PIPE
from tinyscript.helpers import Path


__all__ = ["FilesManager"]


class FilesManager(dict):
    """ Files dictionary for registering files, if necessary downloading them using multiple supported schemes. """
    root_dir = "."

    def _file(self, locator, *args, **kwargs):
        """ Simple local file copier. """
        self[locator] = open(locator.split("://", 1)[1], 'rb')
    
    def _ftp(self, locator, *args, **kwargs):
        """ Simple FTP downloader. """
        scheme = locator.split("://", 1)[0]
        client = [FTP, FTP_TLS][scheme == "ftps"]()
        client.connect(kwargs.pop("host", ""), kwargs.pop("port", 21))
        if scheme == "ftps":
            client.auth()
        usr, pswd = kwargs.pop("user", ""), kwargs.pop("passwd", "")
        if usr != "" and pswd != "":
            client.login(usr, passwd)
        #client.retrbinary(kwargs.pop("cmd", None), kwargs.pop("callback", None))
        #FIXME
    _ftps = _ftp
    
    def _http(self, url, *args, **kwargs):
        """ Simple HTTP downloader. """
        self[url] = requests.get(url, *args, **kwargs).content
    _https = _http
    
    def edit(self, filename):
        """ Edit a file using the configured text editor. """
        #FIXME: edit by calling the locator and manage its local file (e.g. for a URL, point to a temp folder)
        ted = self.console.config['TEXT_EDITOR']
        if which(ted) is None:
            raise ValueError(f"'{ted}' does not exist or is not installed")
        p = Path(self.console.config['WORKSPACE']).joinpath(filename)
        if not p.exists():
            p.touch()
        call([ted, str(p)], stderr=PIPE)
    
    def get(self, locator, *args, **kwargs):
        """ Get a resource. """
        if locator in self.keys() and not kwargs.pop("force", False):
            return self[locator]
        scheme, path = locator.split("://")
        if scheme in ["http", "https"]:
            r = requests.get(locator, *args, **kwargs)
            self[locator] = r.content
            if r.status_code == 403:
                raise ValueError("Forbidden")
        elif scheme in ["ftp", "ftps"]:
            client = [FTP, FTP_TLS][schem == "ftps"]()
            client.connect(kwargs.pop("host", ""), kwargs.pop("port", 21))
            if scheme == "ftps":
                client.auth()
            usr, pswd = kwargs.pop("user", ""), kwargs.pop("passwd", "")
            if usr != "" and pswd != "":
                client.login(usr, passwd)
            client.retrbinary(kwargs.pop("cmd", None), kwargs.pop("callback", None))
            #FIXME
        elif scheme == "file":
            with open(path, 'rb') as f:
                self[locator] = f.read()
        else:
            raise ValueError(f"Unsupported scheme '{scheme}'")
    
    def page(self, *filenames):
        """ Page a list of files using Less. """
        tvw = self.console.config['TEXT_VIEWER']
        if which(tvw) is None:
            raise ValueError(f"'{tvw}' does not exist or is not installed")
        filenames = list(map(str, filenames))
        for f in filenames:
            if not Path(str(f)).is_file():
                raise OSError("File does not exist")
        call([tvw] + filenames, stderr=PIPE)
    
    def page_text(self, text):
        """ Page a text using Less. """
        tmp = self.tempdir.tempfile()
        tmp.write_text(text)
        self.page(str(tmp))
    
    def save(self, key, dst):
        """ Save a resource. """
        with open(dst, 'wb') as f:
            f.write(self[key])
    
    def view(self, key):
        """ View a file using the configured text viewer. """
        from tinyscript.helpers import txt_terminal_render
        try:
            self.page_text(self[key])
        except KeyError:
            pass
        p = Path(self.console.config['WORKSPACE'], expand=True).joinpath(key)
        if p.suffix == ".md":
            self.page_text(txt_terminal_render(p.text, format="md").strip())
        else:
            # if the given key is not in the dictionary of files (APP_FOLDER/files/), it can still be in the workspace
            self.page(p)
    
    @property
    def list(self):
        """ Get the list of files from the workspace. """
        p = Path(self.console.config['WORKSPACE']).expanduser()
        for f in p.walk(filter_func=lambda p: p.is_file(), relative=True):
            if all(not re.match(x, f.filename) for x in ["(data|key|store)\.db.*", "history"]):
                yield f
    
    @property
    def tempdir(self):
        """ Get the temporary directory. """
        from tinyscript.helpers import TempPath
        if not hasattr(self, "_tempdir"):
            self._tempdir = TempPath(prefix=f"{self.console.appname}-", length=16)
        return self._tempdir


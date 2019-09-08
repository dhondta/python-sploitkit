# -*- coding: UTF-8 -*-
import requests
from ftplib import FTP, FTP_TLS
from pypager.pager import Pager
from pypager.source import GeneratorSource
from pyvim.editor import Editor

from ...utils.path import Path, TempPath

__all__ = ["FilesManager"]


class FilesManager(dict):
    """ Files dictionary for registering files, if necessary downloading them
         using multiple supported schemes. """
    root_dir = "."

    def _file(self, locator, *args, **kwargs):
        """ Simple local file copier. """
        with open(locator.split("://", 1)[1], 'rb') as f:
            self[url] = f.read()  #FIXME: use file descriptor
    
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
        #with open(
        #client.retrbinary(kwargs.pop("cmd", None),
        #                  kwargs.pop("callback", None))
        #FIXME

    _ftps = _ftp
    
    def _http(self, url, *args, **kwargs):
        """ Simple HTTP downloader. """
        self[url] = requests.get(url, *args, **kwargs).content

    _https = _http
    
    def edit(self, key, **kwargs):
        """ Edit a file using PyVim. """
        e = Editor(**kwargs)
        e.load_initial_files([filepath])
        e.run()
    
    def get(self, url, *args, **kwargs):
        """ Get a resource. """
        if url in self.keys() and not kwargs.pop("force", False):
            return self[url]
        scheme = url.split("://")[0]
        if scheme in ["http", "https"]:
            r = requests.get(url, *args, **kwargs)
            self[url] = r.content
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
            client.retrbinary(kwargs.pop("cmd", None),
                              kwargs.pop("callback", None))
            #FIXME
        elif scheme == "file":
            with open(url.split("://", 1)[1], 'rb') as f:
                self[url] = f.read()
        else:
            raise ValueError("Unsupported scheme '{}'".format(scheme))
    
    def save(self, key, dst):
        """ Save a resource. """
        with open(dst, 'wb') as f:
            f.write(self[key])
    
    def tempdir(self):
        """ Create a temporary directory. """
        return TempPath(prefix="dronesploit-", length=16)
    
    def tempfile(self, root=None):
        """ Create a temporary file. """
        if root is None or not isinstance(root, Path):
            root = TempPath(prefix="dronesploit-", length=16)
        return root.tempfile()
    
    def view(self, key):
        """ View a file with PyPager. """
        fp = self[key]
        # make a generator for the file
        def _():
            with open(filepath) as f:
                for l in f:
                    yield [('', l)]
        # now start the pager
        from pypager.pager import Pager
        from pypager.source import GeneratorSource
        p = Pager()
        p.add_source(GeneratorSource(_()))
        p.run()

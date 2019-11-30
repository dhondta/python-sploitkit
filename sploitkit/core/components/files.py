# -*- coding: UTF-8 -*-
import requests
from ftplib import FTP, FTP_TLS

from ...utils.misc import edit_file, page_file
from ...utils.path import Path, TempPath

__all__ = ["FilesManager"]


class FilesManager(dict):
    """ Files dictionary for registering files, if necessary downloading them
         using multiple supported schemes. """
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
        #client.retrbinary(kwargs.pop("cmd", None),
        #                  kwargs.pop("callback", None))
        #FIXME

    _ftps = _ftp
    
    def _http(self, url, *args, **kwargs):
        """ Simple HTTP downloader. """
        self[url] = requests.get(url, *args, **kwargs).content

    _https = _http
    
    def edit(self, key):
        """ Edit a file using PyVim. """
        #FIXME
        edit_file(key)
    
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
            client.retrbinary(kwargs.pop("cmd", None),
                              kwargs.pop("callback", None))
            #FIXME
        elif scheme == "file":
            with open(path, 'rb') as f:
                self[locator] = f.read()
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
            root = self.tempdir()
        return root.tempfile()
    
    def view(self, key):
        """ View a file with PyPager. """
        page_text(self[key])

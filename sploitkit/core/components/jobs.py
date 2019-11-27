# -*- coding: UTF-8 -*-
import shlex
from prompt_toolkit.patch_stdout import patch_stdout
from six import string_types
from subprocess import call, Popen, TimeoutExpired, PIPE, STDOUT
from time import time

from sploitkit.core.components.logger import null_logger

__all__ = ["JobsPool"]


communicate = lambda p, **i: tuple(map(lambda x: x.decode().strip(),
                                       p.communicate(**i)))


class JobsPool(object):
    def __init__(self, max_jobs=None):
        self.__jobs = []
        self.max = max_jobs
    
    def background(self, cmd, **kwargs):
        p = self.process(cmd, **kwargs)
        self.__jobs.append(p)
    
    def call(self, cmd, **kwargs):
        kwargs['stdout'], kwargs['stderr'] = PIPE, PIPE
        return call(shlex.split(cmd), **kwargs)
    
    def free(self):
        for p in self.__jobs:
            if p.poll():
                self.__jobs.remove(p)
    
    def process(self, cmd, **kwargs):
        if not kwargs.pop('no_debug', False):
            c = " ".join(cmd) if isinstance(cmd, (tuple, list)) else cmd
            self.logger.debug(c)
        cmd = shlex.split(cmd) if isinstance(cmd, string_types) else cmd
        p = Popen(cmd, stdout=PIPE, **kwargs)
        return p
    
    def run(self, cmd, stdin=None, show=False, timeout=None, **kwargs):
        kwargs['stderr'] = PIPE
        kwargs['stdin'] = (None if stdin is None else PIPE)
        p = self.process(cmd, **kwargs)
        com_kw = {}
        if stdin is not None:
            com_kw['input'] = stdin.encode()
        if timeout is not None:
            com_kw['timeout'] = timeout
        out, err = "", ""
        try:
            out, err = tuple(map(lambda x: x.decode().strip(),
                                 p.communicate(**com_kw)))
        except (KeyboardInterrupt, TimeoutExpired):
            _ = []
            for line in iter(p.stdout.readline, ""):
                _.append(line)
            out = "\n".join(_)
            _ = []
            for line in iter(p.stderr.readline, ""):
                _.append(line)
            err = "\n".join(_)
        if show:
            if out != "":
                self.logger.info(out)
            if err != "":
                self.logger.error(err)
        return out, err
    
    def run_iter(self, cmd, timeout=None, **kwargs):
        kwargs['stderr'] = STDOUT
        kwargs['universal_newlines'] = True
        p = self.process(cmd, **kwargs)
        s = time()
        for line in iter(p.stdout.readline, ""):
            if len(line) > 0:
                yield line
            if timeout is not None and time() - s > timeout:
                break
        try:
            p.kill()
        except:
            pass
    
    def terminate(self):
        for p in self.__jobs:
            p.terminate()
            self.__jobs.remove(p)
    
    @property
    def logger(self):
        if hasattr(self, "console"):
            return self.console.logger
        return null_logger

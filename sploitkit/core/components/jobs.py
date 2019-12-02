# -*- coding: UTF-8 -*-
import shlex
import subprocess
from prompt_toolkit.patch_stdout import patch_stdout
from six import string_types
from time import time

from sploitkit.core.components.logger import null_logger

__all__ = ["JobsPool"]


communicate = lambda p, **i: tuple(map(lambda x: x.decode().strip(),
                                       p.communicate(**i)))


class Job(subprocess.Popen):
    def __init__(self, cmd, **kwargs):
        self.parent = kwargs.pop('parent')
        if not kwargs.pop('no_debug', False):
            c = " ".join(cmd) if isinstance(cmd, (tuple, list)) else cmd
            self.parent.logger.debug(c)
        cmd = shlex.split(cmd) if isinstance(cmd, string_types) else cmd
        super(Job, self).__init__(cmd, stdout=subprocess.PIPE, **kwargs)
    
    def close(self, wait=True):
        for s in ["stdin", "stdout", "stderr"]:
            getattr(getattr(self, s, object()), "close", lambda: None)()
        if wait:
            return self.wait()


class JobsPool(object):
    def __init__(self, max_jobs=None):
        self.__jobs = {None: []}
        self.max = max_jobs
    
    def background(self, cmd, **kwargs):
        subpool = kwargs.pop('subpool')
        self.__jobs.setdefault(subpool, [])
        self.__jobs[subpool].append(Job(cmd, parent=self, **kwargs))
    
    def call(self, cmd, **kwargs):
        kwargs['stdout'] = kwargs['stderr'] = subprocess.PIPE
        return subprocess.call(shlex.split(cmd), **kwargs)
    
    def free(self, subpool=None):
        for p in self.__jobs[subpool]:
            if p.poll():
                p.close(False)
                self.__jobs[subpool].remove(p)
    
    def run(self, cmd, stdin=None, show=False, timeout=None, **kwargs):
        kwargs['stderr'] = subprocess.PIPE
        kwargs['stdin'] = (None if stdin is None else subprocess.PIPE)
        p = Job(cmd, parent=self, **kwargs)
        com_kw = {}
        if stdin is not None:
            com_kw['input'] = stdin.encode()
        if timeout is not None:
            com_kw['timeout'] = timeout
        out, err = "", ""
        try:
            out, err = tuple(map(lambda x: x.decode().strip(),
                                 p.communicate(**com_kw)))
        except (KeyboardInterrupt, subprocess.TimeoutExpired):
            out = []
            for line in iter(p.stdout.readline, ""):
                out.append(line)
            out = "\n".join(out)
            err = []
            for line in iter(p.stderr.readline, ""):
                err.append(line)
            err = "\n".join(err)
        if show:
            if out != "":
                self.logger.info(out)
            if err != "":
                self.logger.error(err)
        return out, err
    
    def run_iter(self, cmd, timeout=None, **kwargs):
        kwargs['stderr'] = subprocess.STDOUT
        kwargs['universal_newlines'] = True
        p = Job(cmd, parent=self, **kwargs)
        s = time()
        try:
            for line in iter(p.stdout.readline, ""):
                if len(line) > 0:
                    yield line
                if timeout is not None and time() - s > timeout:
                    break
        finally:
            p.kill()
            p.close()
    
    def terminate(self, subpool=None):
        for p in self.__jobs[subpool]:
            p.terminate()
            p.close()
            self.__jobs[subpool].remove(p)
    
    @property
    def logger(self):
        if hasattr(self, "console"):
            return self.console.logger
        return null_logger

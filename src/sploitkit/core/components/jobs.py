# -*- coding: UTF-8 -*-
import shlex
import subprocess
from tinyscript.helpers.text import ansi_seq_strip


__all__ = ["JobsPool"]


communicate = lambda p, **i: tuple(map(lambda x: x.decode().strip(), p.communicate(**i)))


class Job(subprocess.Popen):
    """ Subprocess-based job class, bound to its parent pool. """
    def __init__(self, cmd, **kwargs):
        self.parent = kwargs.pop('parent')
        debug = not kwargs.pop('no_debug', False)
        if debug:
            self.parent.logger.debug(" ".join(cmd) if isinstance(cmd, (tuple, list)) else cmd)
        cmd = shlex.split(cmd) if isinstance(cmd, str) and not kwargs.get('shell', False) else cmd
        super(Job, self).__init__(cmd, stdout=subprocess.PIPE, **kwargs)
        self._debug = debug
    
    def close(self, wait=True):
        for s in ["stdin", "stdout", "stderr"]:
            getattr(getattr(self, s, object()), "close", lambda: None)()
        if wait:
            return self.wait()


class JobsPool(object):
    """ Subprocess-based pool for managing open jobs. """
    def __init__(self, max_jobs=None):
        self.__jobs = {None: []}
        self.max = max_jobs
    
    def __iter__(self):
        for j in self.__jobs.items():
            yield j
    
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
    
    def run(self, cmd, stdin=None, show=False, timeout=None, ansi_strip=True, **kwargs):
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
            out, err = tuple(map(lambda x: x.decode().strip(), p.communicate(**com_kw)))
        except (KeyboardInterrupt, subprocess.TimeoutExpired):
            out = []
            for line in iter(p.stdout.readline, ""):
                out.append(line)
            out = "\n".join(out)
            err = []
            for line in iter(p.stderr.readline, ""):
                err.append(line)
            err = "\n".join(err)
        if out != "" and p._debug:
            getattr(self.logger, ["debug", "info"][show])(out)
        if err != "" and p._debug:
            getattr(self.logger, ["debug", "error"][show])(err)
        if ansi_strip:
            out = ansi_seq_strip(out)
        return out, err
    
    def run_iter(self, cmd, timeout=None, ansi_strip=True, **kwargs):
        from time import time
        kwargs['stderr'] = subprocess.STDOUT
        kwargs['universal_newlines'] = True
        p = Job(cmd, parent=self, **kwargs)
        s = time()
        #FIXME: cleanup this part
        def readline():
            while True:
                try:
                    l = p.stdout.readline()
                    if l == "":
                        break
                except UnicodeDecodeError:
                    continue
                yield l
        try:
            for line in readline():
                if len(line) > 0:
                    if p._debug:
                        self.logger.debug(line)
                    if ansi_strip:
                        line = ansi_seq_strip(line)
                    yield line
                if timeout is not None and time() - s > timeout:
                    break
        finally:
            p.kill()
            p.close()
    
    def terminate(self, subpool=None):
        for p in self.__jobs.get(subpool, []):
            p.terminate()
            p.close()
            self.__jobs[subpool].remove(p)
    
    @property
    def logger(self):
        if hasattr(self, "console"):
            return self.console.logger
        from sploitkit.core.components.logger import null_logger
        return null_logger


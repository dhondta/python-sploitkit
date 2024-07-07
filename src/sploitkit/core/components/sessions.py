# -*- coding: UTF-8 -*-
import os


__all__ = ["SessionsManager"]


class Session(object):
    """ Class representing a session object based on a shell command """
    def __init__(self, n, cmd, **kwargs):
        from shlex import split
        from tinyscript.helpers import Path
        self.id = n
        self.parent = kwargs.pop('parent')
        if isinstance(cmd, str):
            cmd = split(cmd)
        self._path = Path(self.parent.console._files.tempdir, "session", str(n), create=True)
        for i, s in enumerate(["stdin", "stdout", "stderr"]):
            fifo = str(self._path.joinpath(str(i)))
            self._named_pipes.append(fifo)
            os.mkfifo(fifo, 0o777)
            setattr(self, "_" + s, os.open(fifo ,os.O_WRONLY))
    
    def close(self):
        from shutil import rmtree
        for s in ["stdin", "stdout", "stderr"]:
            getattr(self, "_" + s).close()
        rmtree(str(self._path))
        self._process.wait()
        del self.parent[self.id]
    
    def start(self, **kwargs):
        from subprocess import Popen
        kwargs['close_fds'] = True
        kwargs['preexec_fn'] = os.setsid  # NB: see subprocess' doc ; preexec_fn is not thread-safe
        self._process = Popen(cmd, stdout=self._stdout, stderr=self._stderr, stdin=self._stdin, **kwargs) 


class SessionsManager(object):
    """ Class for managing session objects. """
    def __init__(self, max_sessions=None):
        self.__sessions = []
        self.max = max_sessions
    
    def __delitem__(self, session_id):
        self.__sessions[sessin_id] = None
        while self.__sessions[-1] is None:
            self.__sessions.pop()
    
    def __getitem__(self, session_id):
        return self.__sessions[int(session_id)]
    
    def __iter__(self):
        for i, s in enumerate(self.__sessions):
            if s is not None:
                yield i, s
    
    def __len__(self):
        n = 0
        for s in self:
            n += 1
        return n
    
    def new(self, session):
        for i, s in enumerate(self.__session):
            if s is None:
                self.__session[i] = session
                return session
        self.__session.append(session)
        return session
    
    def process(self, cmd, **kwargs):
        return self.new(Session(self, i+1, cmd, **kwargs))
    
    def shell(self, shell_cls, *args, **kwargs):
        return self.new(shell_cls(*args, **kwargs))


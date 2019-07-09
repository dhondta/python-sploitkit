from __future__ import unicode_literals

import os
import stat

from sploitkit import Command


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Pydbg(Command):
    """ Start a Python debugger session """
    def run(self):
        import pdb
        pdb.set_trace()


class Shell(Command):
    """ Execute a shell command """
    splitargs = False
    
    def complete_values(self):
        l = []
        e = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
        for p in os.environ['PATH'].split(":"):
            if not os.path.isdir(p):
                continue
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.isfile(fp):
                    st = os.stat(fp)
                    if st.st_mode & e and f not in l:
                        l.append(f)
        return l
        
    def run(self, cmd=None):
        from subprocess import call
        call("/bin/bash" if cmd is None else cmd, shell=True)
        print("")

from __future__ import unicode_literals

from sploitkit import Command


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class Pdb(Command):
    """ Start a Python debugger session """
    def run(self):
        import pdb
        pdb.set_trace()


class Shell(Command):
    """ Execute a shell command """
    splitargs = False

    def run(self, cmd=None):
        from subprocess import call
        call("/bin/bash" if cmd is None else cmd, shell=True)
        print("")

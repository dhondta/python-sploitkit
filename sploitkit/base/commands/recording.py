from __future__ import unicode_literals

from sploitkit import Command, Console
from sploitkit.utils.path import Path


rcfiles = lambda c: [x.name for x in Path(c.console.config['WORKSPACE'])\
                     .expanduser().iterfiles(".rc")]


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class RecordStatus(Command):
    """ Consult status for commands recording to a .rc file """
    # Rationale: recording status should be consultable from any console level
    aliases = ["record"]
    alias_only = True
    values = ["status"]

    def run(self, status):
        _ = ["disabled", "enabled"][Console.parent.recorder.enabled]
        self.logger.info("Recording is {}".format(_))


# ------------------------------ ROOT-LEVEL COMMANDS ---------------------------
class RecordCommand(Command):
    """ Proxy class (namely for setting the level attribute). """
    level = "root"

    def complete_values(self):
        return rcfiles(self)


class Record(RecordCommand):
    """ Start/stop or consult status of commands recording to a .rc file """
    # Rationale: recording start/stop is only triggerable from the root level
    options = ["start", "stop", "status"]
    
    def run(self, option, rcfile=None):
        if option == "start":
            Console._recorder.start(rcfile)
        elif option == "stop":
            Console._recorder.stop()
        elif option == "status":
            _ = ["disabled", "enabled"][Console._recorder.enabled]
            self.logger.info("Recording is {}".format(_))
    
    def validate(self, option, rcfile=None):
        if option == "start":
            assert rcfile is not None, "Please enter a filename"
            assert not Path(rcfile).exists(), \
                   "A file with the same name already exists"
        elif option in ["stop", "status"]:
            assert rcfile is None


class Replay(RecordCommand):
    """ Execute commands from a .rc file """
    def run(self, rcfile):
        self.logger.debug("Replaying commands from file '{}'..."
                          .format(rcfile))
        with open(rcfile) as f:
            for cmd in f:
                Console.parent.execute(cmd, True)

# -*- coding: UTF-8 -*-
from sploitkit import Command
from sploitkit.utils.path import Path


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class RecordStatus(Command):
    """ Consult status for commands recording to a .rc file """
    # Rationale: recording status should be consultable from any console level
    aliases = ["record"]
    alias_only = True
    values = ["status"]

    def run(self, status):
        _ = ["disabled", "enabled"][self.recorder.enabled]
        self.logger.info("Recording is {}".format(_))


# ------------------------------ ROOT-LEVEL COMMANDS ---------------------------
class RootProjectCommand(Command):
    """ Proxy class (for setting the level attribute). """
    level = ["root", "project"]


class Record(RootProjectCommand):
    """ Start/stop or consult status of commands recording to a .rc file """
    # Rationale: recording start/stop is only triggerable from the root level
    keys = ["start", "stop", "status"]

    def complete_values(self, key=None):
        if key == "start":
            return [x.name for x in Path(self.workspace).iterfiles(".rc")]
    
    def run(self, key, rcfile=None):
        if key == "start":
            self.recorder.start(str(Path(self.workspace).joinpath(rcfile)))
        elif key == "stop":
            self.recorder.stop()
        elif key == "status":
            _ = ["disabled", "enabled"][self.recorder.enabled]
            self.logger.info("Recording is {}".format(_))
    
    def validate(self, key, rcfile=None):
        if key == "start":
            if rcfile is None:
                raise ValueError("please enter a filename")
            if Path(self.workspace).joinpath(rcfile).exists():
                raise ValueError("a file with the same name already exists")
        elif key in ["stop", "status"]:
            if rcfile is not None:
                raise ValueError("this key takes no value")


class Replay(RootProjectCommand):
    """ Execute commands from a .rc file """
    def complete_values(self, key=None):
        return [x.name for x in Path(self.workspace).iterfiles(".rc")]

    def run(self, rcfile):
        self.logger.debug("Replaying commands from file '{}'..."
                          .format(rcfile))
        with open(rcfile) as f:
            for cmd in f:
                self.parent.execute(cmd, True)

# -*- coding: UTF-8 -*-
from tinyscript.helpers import Path

from sploitkit import Command


# ---------------------------- GENERAL-PURPOSE COMMANDS ------------------------
class RecordStatus(Command):
    """ Consult status for commands recording to a .rc file """
    # Rationale: recording status should be consultable from any console level
    aliases = ["record"]
    alias_only = True
    except_levels = ["session"]
    values = ["status"]

    def run(self, status):
        self.logger.info(f"Recording is {['disabled', 'enabled'][self.recorder.enabled]}")


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
            self.logger.info(f"Recording is {['disabled', 'enabled'][self.recorder.enabled]}")
    
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
        self.logger.debug(f"Replaying commands from file '{rcfile}'...")
        self.console.replay(rcfile)


# -*- coding: UTF-8 -*-
from sploitkit import *


# ----------------------------- SUBCONSOLE DEFINITION --------------------------
class SessionConsole(Console):
    """ Session subconsole definition. """
    level = "session"
    message_reset = True
    message = [
        ('class:session', None),
        ('class:prompt', ">"),
    ]
    style = {
        'prompt': "#eeeeee",
        'session': "#00ff00",
    }
    
    def __init__(self, parent, session_id):
        session = parent._sessions[session_id]
        self.logname = "session-%d" % session_id
        self.message[0] = ('class:prompt', session.name)
        super(SessionConsole, self).__init__(parent, fail=False)
        self.config.prefix = "Module"


# ---------------------------- SESSION-RELATED COMMANDS ------------------------
class Background(Command):
    """ Put the current session to the background """
    level = "session"
    
    def run(self):
        # do something with the session
        raise ConsoleExit


class Session(Command):
    """ Resume an open session """
    except_levels = ["session"]
    #requirements = {'internal': lambda s: len(s.console._sessions) > 0}
    
    def complete_values(self):
        return list(range(len(self.console._sessions)))
    
    def run(self, session_id):
        SessionConsole(self.console, session_id).start()


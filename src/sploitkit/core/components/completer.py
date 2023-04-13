# -*- coding: UTF-8 -*-
from prompt_toolkit.completion import Completer, Completion


__all__ = ["CommandCompleter"]


def _filter_sort(lst, prefix=None, sort=False):
    if sort:
        lst = sorted(map(str, set(lst or [])), key=lambda s: str(s).casefold())
    for x in lst or []:
        if prefix is None or x.startswith(prefix):
            yield x


class CommandCompleter(Completer):
    """ Completer for console's commands and arguments. """
    def get_completions(self, document, complete_event):
        # this completion method handles the following formats:
        #  1) COMMAND VALUE     ; e.g. create my-project
        #  2) COMMAND KEY VALUE ; e.g. set LHOST 192.168.1.1
        # first, tokenize document.text and initialize some shorcut variables
        d = document.text
        tokens = self.console._get_tokens(d)
        l = len(tokens)
        ts = len(d) - len(d.rstrip(" "))  # trailing spaces
        try:
            cmd, t1, t2 = tokens + [None] * (3 - l)
        except:     # occurs when l > 3 ; no need to complete anything as it corresponds to an invalid command
            return
        bc = len(document.text_before_cursor)
        it = len(d) - bc > 0
        o1 = len(cmd) + 1 - bc if cmd else 0
        o2 = len(cmd) + len(t1 or "") + 2 - bc if cmd and t2 else 0
        cmds = {k: v for k, v in self.console.commands.items()}
        c = cmds[cmd]._instance if cmd in cmds else None
        nargs = len(c.args) if c is not None else 0
        # then handle tokens ;
        # when no token is provided, just yield the list of available commands
        if l == 0:
            for x in _filter_sort(cmds.keys(), sort=True):
                yield Completion(x, start_position=0)
        # when one token is provided, handle format:
        #   [PARTIAL_]COMMAND ...
        elif l == 1:
            # when a partial token is provided, yield the list of valid commands
            if ts == 0 and c not in cmds:
                for x in _filter_sort(cmds, cmd, True):
                    yield Completion(x, start_position=-bc)
            # when a valid command is provided, yield the list of valid keys or values, depending on the type of command
            elif ts > 0 and c is not None:
                if nargs == 1:    # COMMAND VALUE
                    for x in _filter_sort(c._complete_values(), sort=True):
                        yield Completion(x, start_position=0)
                # e.g.  set  ---> ["WORKSPACE", ...]
                elif nargs == 2:  # COMMAND KEY VALUE
                    for x in _filter_sort(c._complete_keys(), sort=True):
                        yield Completion(x, start_position=0)
        # when two tokens are provided, handle format:
        #   COMMAND [PARTIAL_](KEY ...|VALUE)
        elif l == 2 and c is not None:
            # when a partial value token is given, yield the list of valid ones
            # e.g.  select my-pro  ---> ["my-project", ...]
            if nargs == 1 and ts == 0:
                for x in _filter_sort(c._complete_values(), t1, True):
                    yield Completion(x, start_position=o1)
            # when a partial key token is given, yield the list of valid ones
            # e.g.  set W  ---> ["WORKSPACE"]
            elif nargs == 2 and ts == 0:
                for x in _filter_sort(c._complete_keys(), t1, True):
                    yield Completion(x, start_position=o1)
            # when a valid key token is given, yield the list of values
            # e.g.  set WORKSPACE  ---> ["/home/user/...", "..."]
            elif nargs == 2 and ts > 0 and t1 in c._complete_keys():
                for x in _filter_sort(c._complete_values(t1), sort=True):
                    yield Completion(x, start_position=0)
        # when three tokens are provided, handle format:
        #   COMMAND KEY [PARTIAL_]VALUE
        elif l == 3 and c is not None and t1 in c._complete_keys():
            if nargs == 2 and ts == 0:
                for x in _filter_sort(c._complete_values(t1), t2, True):
                    yield Completion(x, start_position=o2)
        # handle no other format


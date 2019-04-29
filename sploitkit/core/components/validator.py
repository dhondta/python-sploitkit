from __future__ import unicode_literals

import shlex
from inspect import getargspec
from prompt_toolkit.validation import Validator, ValidationError


__all__ = ["CommandValidator"]


def get_tokens(text, suffix=("", "\"", "'")):
    """ Recursive token split function handling ' and ". """
    try:
        return shlex.split(text + suffix[0])
    except ValueError:
        return get_tokens(text, suffix[1:])
    except IndexError:
        return []


class CommandValidator(Validator):
    """ Completer for console's commands and arguments. """
    def validate(self, document):
        # first, tokenize document.text
        tokens = get_tokens(document.text.strip())
        l = len(tokens)
        # then handle tokens
        commands = self.console.commands
        # when no token provided, do nothing
        if l == 0:
            return
        # when a command is being typed, mention if it is existing
        cmd = tokens[0]
        if l == 1 and cmd not in commands.keys():
            raise ValidationError(message="Non-existent command")
        # when a valid first token is provided, handle command's validation, if
        #  any available
        elif l >= 1 and cmd in commands.keys():
            c = commands[cmd]()
            try:
                c.validate(*tokens[1:])
            except Exception as e:
                m = "Command syntax: %s{}" % c.signature.format(cmd)
                e = str(e)
                if not str(e).startswith("validate() "):
                    m = m.format([" (" + e + ")", ""][len(e) == 0])
                else:
                    m = m.format("")
                raise ValidationError(message=m)
        # otherwise, the command is considered bad
        else:
            raise ValidationError(message="Bad command")

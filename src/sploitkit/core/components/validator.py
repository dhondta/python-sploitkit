# -*- coding: UTF-8 -*-
from prompt_toolkit.validation import Validator, ValidationError


__all__ = ["CommandValidator"]


class CommandValidator(Validator):
    """ Completer for console's commands and arguments. """
    def __init__(self, fail=True):
        self._fail = fail
        super(CommandValidator, self).__init__()
    
    def validate(self, document):
        # first, tokenize document.text
        tokens = self.console._get_tokens(document.text.strip())
        l = len(tokens)
        # then handle tokens
        commands = self.console.commands
        # when no token provided, do nothing
        if l == 0:
            return
        # when a command is being typed, mention if it is existing
        cmd = tokens[0]
        if l == 1 and cmd not in commands.keys() and self._fail:
            raise ValidationError(message="Unknown command")
        # when a valid first token is provided, handle command's validation, if any available
        elif l >= 1 and cmd in commands.keys():
            c = commands[cmd]._instance
            try:
                c._validate(*tokens[1:])
            except Exception as e:
                m = f"Command syntax: {c.signature.format(cmd)}" 
                e = str(e)
                if not e.startswith("validate() "):
                    m = m.format([" (" + e + ")", ""][len(e) == 0])
                else:
                    m = m.format("")
                raise ValidationError(message=m)
        # otherwise, the command is considered bad
        elif self._fail:
            raise ValidationError(message="Bad command")


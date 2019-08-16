# -*- coding: UTF-8 -*-
import termcolor
from terminaltables.terminal_io import terminal_size as termsize
from textwrap import wrap

__all__ = ["AsciiQuote"]

# little patch to available attributes ; may not work for some terminals
termcolor.ATTRIBUTES['italic'] = 3
termcolor.ATTRIBUTES['strikethrough'] = 9

TERM_WIDTH = int(termsize()[0] * .8)


class AsciiQuote(object):
    """ Quote as an ASCII art.
    
    This converts a quote to an ASCII art using Cowsay if needed and available.
     
    :param quote:      quote to be displayed
    :param source:     quote's source
    :param width:      desired width in characters
    """
    def __init__(self, quote, source=None, width=TERM_WIDTH, cowsay=True):
        self.quote = quote
        self.source = source
        self.width = width
        self.cowsay = cowsay
        #TODO: implement cowsay
    
    def __str__(self):
        q = termcolor.colored(self.quote, attrs=['italic'])
        s = termcolor.colored(self.source, attrs=['dark']).rjust(self.width)
        return wrap("\"{}\",".format(q, self.width)) + "\n" + s

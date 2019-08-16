# -*- coding: UTF-8 -*-
from os.path import dirname, join
from random import choice
from pyfiglet import Figlet, FigletFont, FontNotFound
from terminaltables.terminal_io import terminal_size as termsize


__all__ = ["AsciiBanner"]

TERM_WIDTH = termsize()[0]


with open(join(dirname(__file__), "fonts.txt")) as f:
    FONTS = list(set(f.read().splitlines()))


class AsciiBanner(object):
    """ Banner as an ASCII art.
    
    This converts a text to an ASCII banner using PyFiglet.
     
    This class is inspired from:
      https://github.com/ajalt/pyasciigen/blob/master/asciigen.py
    
    :param text:       text to be displayed
    :param width:      desired width in characters
    :param font:       name of a custom font
    :param multiline:  whether the output should be accepted even if the text is
                        generated on multiple lines
    :param autofont:   automatically choose a replacement font if multiline is
                        False and the output has multiple lines
    """
    def __init__(self, text, width=TERM_WIDTH, font=None, multiline=False,
                 autofont=True):
        self.text = text
        self.width = width
        self.font = font
        self.multiline = multiline
        self._autofont = autofont
    
    def __str__(self):
        # determine the height of a single char
        _ = Figlet(font=self.font, width=TERM_WIDTH).renderText("X")
        h = len(str(_).splitlines())
        # now check that there is no more than a single line
        _ = Figlet(font=self.font, width=self.width)
        s = str(_.renderText(self.text))
        if not self.multiline and len(s.splitlines()) > int(h * 1.5):
            if self._autofont and len(self.__fonts) > 0:
                self.__fonts.remove(self.font)
                self.__font = choice(self.__fonts)
                return str(self)
            else:
                raise ValueError("Font too big or text too large for a single"
                                 " line")
        return s
    
    @property
    def font(self):
        return self.__font
    
    @font.setter
    def font(self, name):
        if name is None:
            name = choice(FONTS)
            while not AsciiBanner.font_exists(name) and len(FONTS) > 0:
                name = choice(FONTS)
            if len(FONTS) == 0:
                raise ValueError("No valid font found")
        elif name not in FONTS:
            raise ValueError("Bad font name")
        self.__font = name
        self.__fonts = FONTS[:]
    
    @staticmethod
    def font_exists(font):
        try:
            Figlet(font=font)
            return True
        except FontNotFound:
            FONTS.remove(font)
            return False

# -*- coding: UTF-8 -*-
import csv
import random
import string
import termcolor
from collections import OrderedDict
from termcolor import colored
from terminaltables.terminal_io import terminal_size as termsize
from textwrap import wrap
try:
    import colorama
    _color_enabled = True
    COLORS = list(vars(colorama.Fore).values())
except ImportError:
    _color_enabled = False

from ...utils.misc import failsafe
from ...utils.path import Path, RandPath


__all__ = ["center", "get_banner", "get_quote"]

# little patch to available attributes ; may not work for some terminals
termcolor.ATTRIBUTES['italic'] = 3
termcolor.ATTRIBUTES['strikethrough'] = 9

center = lambda t: "\n".join(l.center(termsize()[0]) for l in t.split("\n"))


class Banner(object):
    """ Banner representation. """
    def __init__(self, text, colorize=()):
        if not all(c in string.printable for c in text):
            raise ValueError("Invalid banner")
        self.__sections = s = OrderedDict()
        self.__colorize = colorize
        section = "main"
        for l in text.split("\n"):
            s.setdefault(section, "")
            if l.startswith(".section: "):
                section = l.split(":", 1)[1].strip()
            else:
                s[section] += l.center(termsize()[0])

    def __str__(self):
        t = ""
        for k, v in self.__sections.items():
            if _color_enabled and k in self.__colorize:
                v = "".join(random.choice(COLORS) + c for c in v)
            t += v + "\x1b[37m"
        return t


@failsafe
def get_banner(folder, colorize=()):
    """
    Get a random file from the given folder and, if it only consists of
     printable characters, consider it as a banner to be returned.
    
    :param folder: where the banners shall be searched for
    """
    folder = RandPath(Path(folder, expand=True))
    with folder.choice(".asc").open() as f:
        banner = Banner(f.read(), colorize)
    return "\n" + str(banner) + "\n\n"


@failsafe
def get_quote(folder):
    """
    Get a random file from the given folder and, if it only consists of
     printable characters, consider it as a banner to be returned.
    
    :param folder: where the quotes.csv file shall be searched for
    """
    quotes = Path(folder).joinpath("quotes.csv")
    # first, count number of rows
    with quotes.open('rb') as f:
        l = sum(1 for row in csv.reader(f))
    # then choose a random row index and get it
    i = random.randrange(0, l)
    with quotes.open('rb') as f:
        reader = csv.reader(f)
        headers = next(reader)
        i_a, i_q = headers.index('author'), headers.index('quote')
        for j, row in enumerate(reader):
            if i == j:
                quote = row[i_a], row[i_q]
                break
    if not all(c in string.printable for x in quote for c in x):
        raise ValueError("Invalid quote")
    w, h = termsize()
    lw = int(.8 * w)
    quote = wrap("\"{}\",".format(colored(quote[1], attrs=['italic'])), lw) \
            + "\n" + colored(quote[0], attrs=['dark']).rjust(lw)
    return "\n" + center(quote) + "\n\n"

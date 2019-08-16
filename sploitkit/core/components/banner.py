# -*- coding: UTF-8 -*-
import csv
import random
import string
import termcolor
from collections import Counter, OrderedDict
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from termcolor import colored
from terminaltables.terminal_io import terminal_size as termsize
from textwrap import wrap
try:
    import colorama
    _color_enabled = True
    COLORS = list(vars(colorama.Fore).values())
except ImportError:
    _color_enabled = False

from ...utils.asciiart import *
from ...utils.misc import failsafe
from ...utils.path import Path


__all__ = ["center", "get_banner", "get_quote"]

# little patch to available attributes ; may not work for some terminals
termcolor.ATTRIBUTES['italic'] = 3
termcolor.ATTRIBUTES['strikethrough'] = 9

center = lambda t: "\n".join(l.center(termsize()[0]) for l in t.split("\n"))


#@failsafe
def get_banner(text=None, folder=None, secstyles={}):
    """
    Display an ASCII art banner.
    
    If text is not None, generate an ASCII art and use it only if 
    
    :param text:   text to be displayed
    :param folder: where the banners shall be searched for
    """
    if folder is None:
        if text is None:
            return
        asc = AsciiFile()
        asc["title", secstyles.get("title", {})] = AsciiBanner(text)
    else:
        p = Path(folder).choice(".asc", ".jpg", ".jpeg", ".png")
        if p.suffix == ".asc":
            asc = AsciiFile(p)
            if asc.get("title") is None and text is not None:
                _ = AsciiFile()
                _["title", secstyles.get("title", {})] = AsciiBanner(text)
                for k, v, p in asc.items():
                    _[k, p] = v
                asc = _
        elif p.suffix in [".jpg", ".jpeg", ".png"]:
            asc = AsciiFile()
            if text is not None:
                asc["title", secstyles.get("title", {})] = AsciiBanner(text)
            asc["logo", secstyles.get("logo", {})] = AsciiImage(p)
            asc["logo"][0].height = 5
        else:
            return get_banner(text, None, secstyles)
    return str(asc)


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

from __future__ import unicode_literals

import csv
import random
import string
import termcolor
from termcolor import colored
from terminaltables.terminal_io import terminal_size as termsize
from textwrap import wrap

from ...utils.misc import failsafe
from ...utils.path import Path, RandPath


__all__ = ["center", "get_banner", "get_quote"]

# little patch to available attributes ; may not work for some terminals
termcolor.ATTRIBUTES['italic'] = 3
termcolor.ATTRIBUTES['strikethrough'] = 9

center = lambda t: "\n".join(l.center(termsize()[0]) for l in t.split("\n"))


@failsafe
def get_banner(folder):
    """
    Get a random file from the given folder and, if it only consists of
     printable characters, consider it as a banner to be returned.
    
    :param folder: where the banners shall be searched for
    """
    folder = RandPath(Path(folder).expanduser())
    with folder.choice(".asc").open() as f:
        banner = f.read()
    assert all(c in string.printable for c in banner)
    return "\n" + center(banner) + "\n\n"


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
    assert all(c in string.printable for x in quote for c in x)
    w, h = terminal_size()
    lw = int(.8 * w)
    quote = wrap("\"{}\",".format(colored(quote[1], attrs=['italic'])), lw) \
            + "\n" + colored(quote[0], attrs=['dark']).rjust(lw)
    return "\n" + center(quote) + "\n\n"

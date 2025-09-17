#!/usr/bin/python3
import site
site.addsitedir("../src")

from sploitkit import FrameworkConsole
from tinyscript import *


class MySploitConsole(FrameworkConsole):
    #TODO: set your console attributes
    pass


if __name__ == '__main__':
    parser.add_argument("-d", "--dev", action="store_true", help="enable development mode")
    parser.add_argument("-r", "--rcfile", type=ts.file_exists, help="execute commands from a rcfile")
    initialize()
    c = MySploitConsole(
        "MySploit",
        #TODO: configure your console settings
        dev=args.dev,
    )
    c.rcfile(args.rcfile) if args.rcfile else c.start()

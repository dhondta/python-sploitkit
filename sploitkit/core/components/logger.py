# -*- coding: utf8 -*-
import logging
from logging.handlers import RotatingFileHandler
from termcolor import colored


__all__ = ["get_logger"]


logging.SUCCESS = logging.INFO + 5
DATE_FORMAT = "%m/%d/%y %H:%M:%S"
LOGFILE_FORMAT = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"
LOG_FORMAT = "%(levelsymbol)s %(message)s"
LOG_LEVEL_SYMBOLS = {
    logging.INFO:    colored("[*]", "blue"),
    logging.SUCCESS: colored("[+]", "green", attrs=['bold']),
    logging.WARNING: colored("[!]", "yellow"),
    logging.ERROR:   colored("[-]", "red", attrs=['bold']),
    logging.DEBUG:   colored("[#]", "white"),
    None:            colored("[?]", "grey"),
}


# this avoids throwing e.g. FutureWarning or DeprecationWarning messages
logging.captureWarnings(True)
logger = logging.getLogger('py.warnings')
logger.setLevel(logging.CRITICAL)


# silent sh module's logging
logger = logging.getLogger('sh.command')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.streamreader')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.stream_bufferer')
logger.setLevel(level=logging.WARNING)


# add a custom log level for stepping
logging.addLevelName(logging.SUCCESS, "SUCCESS")
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.SUCCESS):
        self._log(logging.SUCCESS, message, args, **kwargs) 
logging.Logger.success = success


# add a custom message handler for tuning the format with 'levelsymbol'
class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        record.levelsymbol = LOG_LEVEL_SYMBOLS.get(record.levelno, "")
        super(ConsoleHandler, self).emit(record)


# logging configuration
def get_logger(name, logfile):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # setup a StreamHandler for the console (at level INFO)
    ch = ConsoleHandler()
    ch.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    # setup a FileHandler for logging to a file (at level DEBUG)
    fh = RotatingFileHandler(logfile)
    fh.setFormatter(logging.Formatter(LOGFILE_FORMAT, datefmt=DATE_FORMAT))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    return logger

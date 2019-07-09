# -*- coding: utf8 -*-
import logging
from logging.handlers import RotatingFileHandler
from termcolor import colored


__all__ = ["check_log_level", "get_logger", "null_handler"]


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


# set a null logger
null_handler = logging.getLogger("main")
null_handler.addHandler(logging.NullHandler())


# add a custom message handler for tuning the format with 'levelsymbol'
class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        record.levelsymbol = LOG_LEVEL_SYMBOLS.get(record.levelno, "")
        super(ConsoleHandler, self).emit(record)


# log level checking
def check_log_level(level):
    """ Log level check function. """
    try:
        return isinstance(getattr(logging, level), int)
    except:
        return False


# logging configuration
def get_logger(name, logfile=None, level="INFO"):
    """ Logger initialization function. """
    logger = logging.getLogger(name)
    level = getattr(logging, level)
    logger.setLevel(level)
    if len(logger.handlers) == 0:
        # setup a StreamHandler for the console (at level INFO)
        ch = ConsoleHandler()
        ch.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
        ch.setLevel(level)
        logger.addHandler(ch)
        if logfile is not None:
            # setup a FileHandler for logging to a file (at level DEBUG)
            fh = RotatingFileHandler(logfile)
            fh.setFormatter(logging.Formatter(LOGFILE_FORMAT, datefmt=DATE_FORMAT))
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)
    else:
        for h in logger.handlers:
            h.setLevel(level)
    return logger

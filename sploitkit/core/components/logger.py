# -*- coding: utf8 -*-
import logging
from logging.handlers import RotatingFileHandler
from termcolor import colored


__all__ = ["get_logger", "null_logger"]


SUCCESS           = logging.ERROR + 1
DATETIME_FORMAT   = "%m/%d/%y %H:%M:%S"
LOGFILE_FORMAT    = "%(asctime)s [%(process)5d] %(levelname)8s %(name)s - " \
                    "%(message)s"
LOG_FORMAT        = "%(levelsymbol)s %(message)s"
LOG_LEVEL_SYMBOLS = {
    logging.DEBUG:    colored("[#]", "white"),
    logging.INFO:     colored("[*]", "blue"),
    logging.WARNING:  colored("[!]", "yellow"),
    SUCCESS:          colored("[+]", "green", attrs=['bold']),
    logging.ERROR:    colored("[-]", "red", attrs=['bold']),
    logging.CRITICAL: colored("[X]", "red", attrs=['bold']),
    None:             colored("[?]", "grey"),
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


# define a specific logger class
class SploitkitLogger(logging.Logger):
    pass


# add custom log levels
def failure(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.ERROR):
        self._log(logging.ERROR, message, args, **kwargs) 
SploitkitLogger.failure = failure
logging.addLevelName(SUCCESS, "SUCCESS")
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kwargs) 
SploitkitLogger.success = success


# set a null logger
null_logger = logging.getLogger("main")
null_logger.addHandler(logging.NullHandler())


# add a custom message handler for tuning the format with 'levelsymbol'
class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        record.levelsymbol = LOG_LEVEL_SYMBOLS.get(record.levelno, "")
        super(ConsoleHandler, self).emit(record)


# logging configuration
def get_logger(name, logfile=None, level="INFO"):
    """ Logger initialization function. """
    tmp = logging.getLoggerClass()
    logging.setLoggerClass(SploitkitLogger)
    logger = logging.getLogger(name)
    level = getattr(logging, level)
    logger.setLevel(logging.DEBUG)
    if len(logger.handlers) == 0:
        # setup a StreamHandler for the console (at level INFO)
        ch = ConsoleHandler()
        ch.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
        ch.setLevel(level)
        logger.addHandler(ch)
        if logfile is not None:
            logger.__logfile__ = logfile
            # setup a FileHandler for logging to a file (at level DEBUG)
            fh = RotatingFileHandler(logfile)
            fh.setFormatter(logging.Formatter(LOGFILE_FORMAT,
                                              datefmt=DATETIME_FORMAT))
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)
        else:
            logger.__logfile__ = None
    else:
        for h in logger.handlers:
            h.setLevel(level)
    logging.setLoggerClass(tmp)
    return logger

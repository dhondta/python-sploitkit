# -*- coding: utf8 -*-
from tinyscript import colored, logging


__all__ = ["get_logger", "null_logger", "set_logging_level"]


DATETIME_FORMAT   = "%m/%d/%y %H:%M:%S"
LOGFILE_FORMAT    = "%(asctime)s [%(process)5d] %(levelname)8s %(name)s - %(message)s"
LOG_FORMAT        = "%(levelsymbol)s %(message)s"
LOG_FORMAT_DBG    = "%(asctime)s %(name)32s %(levelname)8s %(message)s"
LOG_LEVEL_SYMBOLS = {
    logging.DETAIL:   colored("[#]", "white"),  # this is aimed to provide even more info in dev mode
    logging.DEBUG:    colored("[#]", "white"),  # this is aimed to be used in normal mode
    logging.INFO:     colored("[*]", "blue"),
    logging.WARNING:  colored("[!]", "yellow"),
    logging.SUCCESS:  colored("[+]", "green", attrs=['bold']),
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


# make aliases from logging functions
null_logger       = logging.nullLogger
set_logging_level = logging.setLoggingLevel


# add a custom message handler for tuning the format with 'levelsymbol'
class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        record.levelsymbol = LOG_LEVEL_SYMBOLS.get(record.levelno, "")
        super(ConsoleHandler, self).emit(record)


# logging configuration
def get_logger(name, logfile=None, level="INFO", dev=False, enabled=True):
    """ Logger initialization function. """
    def _setup_logfile(l):
        from logging.handlers import RotatingFileHandler
        if logfile is not None and not any(isinstance(h, RotatingFileHandler) for h in l.handlers):
            l.__logfile__ = logfile
            # setup a FileHandler for logging to a file (at level DEBUG)
            fh = RotatingFileHandler(logfile)
            fh.setFormatter(logging.Formatter(LOGFILE_FORMAT, datefmt=DATETIME_FORMAT))
            fh.setLevel(level)
            l.addHandler(fh)
        else:
            l.__logfile__ = None
    
    logger = logging.getLogger(name)
    logger.propagate = False
    level = getattr(logging, level) if not isinstance(level, int) else level
    # distinguish dev and framework-bound logger formats
    if dev:
        if enabled:
            # in dev mode, get a logger as of the native library
            logging.configLogger(logger, level, relative=True, fmt=LOG_FORMAT_DBG)
            _setup_logfile(logger)
        else:
            logger.setLevel(1000)
    else:
        # now use the dedicated class for the logger to be returned
        logger.setLevel(level)
        if len(logger.handlers) == 0:
            # setup a StreamHandler for the console (at level INFO)
            ch = ConsoleHandler()
            ch.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
            ch.setLevel(level)
            logger.addHandler(ch)
            _setup_logfile(logger)
        else:
            for h in logger.handlers:
                h.setLevel(level)
    return logger


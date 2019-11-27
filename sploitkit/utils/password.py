# -*- coding: utf8 -*-
"""
Module for input of a password compliant with a simple password policy.

Policy:
- Prevents from using a few conjunction characters (i.e. whitespace, tabulation,
   newline)
- Use passwords of 8 to 40 characters (lengths by default)
- Use at least one lowercase character
- Use at least one uppercase character
- Use at least one digit
- Use at least one special character
- Do not use a password known in a dictionary (e.g. this of John the Ripper)
"""

import string
from getpass import getpass

from .misc import catch_logger


__all__ = ["input_password"]


@catch_logger
def input_password(silent=False, bypass=False, length=(8, 40),
                   bad=["/usr/local/share/john/password.lst",
                        "/usr/share/john/password.lst",
                        "/opt/john/run/password.lst"]):
    """
    This function allows to enter a password enforced with a small password
     policy.

    :param silent: if True, do not print error messages
    :param bypass: if True, do not check the input password (i.e. useful if we
                    want to load something requiring a password not compliant
                    with the password policy hereafter)
    :param length: pair of lower/upper bounds for password length
    :param bad:    path to lists of bad passwords
    :return:       policy-compliant password
    """
    pwd, error = None, False
    if bypass:
        return
    while pwd is None:
        logger.debug("Special conjunction characters are stripped")
        try:
            pwd = getpass("Please enter the password: ").strip()
        except KeyboardInterrupt:
            print("")
            break
        # check for undesired characters
        BAD_CHARS = " \n\t\"\'"
        if any(c in pwd for c in BAD_CHARS):
            if not silent:
                logger.error("Please do not use the following characters [{}]"
                             .format(repr(BAD_CHARS).strip("'")))
            error = True
        # check for length
        if len(pwd) < length[0]:
            if not silent:
                logger.error("Please enter a password of at least {} characters"
                             .format(length[0]))
            error = True
        elif len(pwd) > length[1]:
            if not silent:
                logger.error("Please enter a password of at most {} characters"
                             .format(length[1]))
            error = True
        # check for complexity
        if not any(map(lambda x: x in string.ascii_lowercase, pwd or "")):
            if not silent:
                logger.error("Please enter at least one lowercase character")
            error = True
        if not any(map(lambda x: x in string.ascii_uppercase, pwd or "")):
            if not silent:
                logger.error("Please enter at least one uppercase character")
            error = True
        if not any(map(lambda x: x in string.digits, pwd or "")):
            if not silent:
                logger.error("Please enter at least one digit")
            error = True
        if not any(map(lambda x: x in string.punctuation, pwd or "")):
            if not silent:
                logger.error("Please enter at least one special character")
            error = True
        # check for bad passwords
        found = False
        for fp in bad:
            if found:
                break
            try:
                with open(fp) as f:
                    for l in f:
                        if pwd == l.strip():
                            found = True
                            break
            except IOError:
                continue
        if found:
            if not silent:
                logger.error("Please enter a more complex password")
            error = True
        # finally, set the flags
        if error:
            pwd = None
            error = False
    return pwd

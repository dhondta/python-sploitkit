# -*- coding: utf8 -*-
import os
import shutil
from os.path import abspath, dirname, isdir, join, relpath
from pyminizip import *

from .misc import catch_logger
from .password import input_password


__all__ = ["load_from_archive", "save_to_archive"]

LENGTH = (8, 64)


@catch_logger
def load_from_archive(src_arch, dst_path, pwd=None, ask=False, remove=False):
    """
    This function decompresses the given archive, eventually given a password.

    :param src_arch: path to the archive
    :param dst_path: path where the archive is to be extracted
    :param pwd:      password string to be passed
    :param ask:      whether a password should be asked or not
    :param remove:   remove after decompression
    """
    # handle password then decompress with 7-zip
    pwd = input_password(silent=True, length=LENGTH, logger=logger) \
          if ask else pwd
    logger.debug("Loading {}archive".format(["encrypted ", ""][pwd is None]))
    logger.debug("> Decompressing '{}' to '{}'...".format(src_arch, dst_path))
    try:
        # Pyminizip changes the current working directory after extraction of an
        #  archive ; so backup the current working directory to restore it after
        #  decompression
        cwd = os.getcwd()
        uncompress(src_arch, pwd or "", dst_path, False)
        os.chdir(cwd)
        if remove:
            os.remove(src_arch)
        return True
    except Exception as e:
        logger.error("Bad password" if "error -3" in str(e) else str(e))
        return False


@catch_logger
def save_to_archive(src_path, dst_arch, pwd=None, ask=False, remove=False):
    """
    This function compresses the content of the given source path into the given
     archive as the destination path, eventually given a password.

    :param src_path: path to the content to be archived
    :param dst_arch: path where the archive is to be saved
    :param pwd:      password string to be passed
    :param ask:      whether a password should be asked or not
    :param remove:   remove after compression
    """
    # handle password then compress with 7-zip
    src = abspath(src_path)
    pwd = input_password(length=LENGTH, logger=logger) if ask else pwd
    logger.debug("Saving {}archive".format(["encrypted ", ""][pwd is None]))
    logger.debug("> Compressing '{}' to '{}'...".format(src_path, dst_arch))
    src_list, dst_list = [], []
    for root, dirs, files in os.walk(src):
        for f in files:
            src_list.append(join(root, f))
            dst_list.append(relpath(root, dirname(src)))
    try:
        # Pyminizip changes the current working directory after creation of an
        #  archive ; so backup the current working directory to restore it after
        #  compression
        cwd = os.getcwd()
        compress_multiple(src_list, dst_list, dst_arch, pwd or "", 9)
        os.chdir(cwd)
        if remove:
            shutil.rmtree(src_path) if isdir(src_path) else os.remove(src_path)
        return True
    except OSError as e:
        logger.error(str(e))
        return False

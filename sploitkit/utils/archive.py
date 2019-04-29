# -*- coding: utf8 -*-
from __future__ import print_function
"""
Module for handling (un)encrypted archives using 7-zip (package '7z'). It
 provides functions for saving and loading such archives.
"""

import logging
import os
import shutil
from os.path import isdir, join
from subprocess import Popen, PIPE

from .password import input_password


__all__ = [
    'load_from_archive',
    'save_to_archive',
]

__author__ = "Alexandre D'Hondt"


logger = logging.getLogger('root')


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
    pwd = input_password(silent=True) if ask else pwd
    logger.debug("Loading {}archive".format(["encrypted ", ""][pwd is None]))
    logger.debug("> Decompressing '{}' to '{}'...".format(src_arch, dst_path))
    cmd = ["7z", "x"] + [["-p{}".format(pwd)], []][pwd is None] + \
          ["-o{}".format(dst_path), "-y", src_arch]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if err.strip() != '':
        logger.error(err)
    elif remove:
        os.remove(src_arch)


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
    pwd = input_password() if ask else pwd
    logger.debug("Saving {}archive".format(["encrypted ", ""][pwd is None]))
    logger.debug("> Compressing '{}' to '{}'...".format(src_path, dst_arch))
    cmd = ["7z", "a"] + [["-p{}".format(pwd)], []][pwd is None] + \
          ["-y", dst_arch, src_path]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if err.strip() != '':
        logger.error(err)
    elif remove:
        shutil.rmtree(src_path) if isdir(src_path) else os.remove(src_path)

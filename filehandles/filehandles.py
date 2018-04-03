#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
filehandles.filehandles
~~~~~~~~~~~~~~~~~~~~~~~

This module provides routines for reading files from difference kinds of sources:
   * Single file on a local machine.
   * Directory containing multiple files.
   * Compressed zip/tar archive of files.
   * URL address of file.
"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import io
import sys
import re
import zipfile
import tarfile
import bz2
import gzip
from contextlib import closing
import logging

import verboselogs


if sys.version_info.major == 3:
    from urllib.request import urlopen
    from urllib.parse import urlparse
else:
    import bz2file as bz2
    from urllib2 import urlopen
    from urlparse import urlparse

    class NotADirectoryError(OSError):
        """Operation only works on directories."""

        def __init__(self, *args, **kwargs):
            pass


# Set verbose logger
logger = verboselogs.VerboseLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.VERBOSE)


openers = []  # openers are added at the import time by @register decorator


class GZValidationError(Exception):
    """Raises exception if not valid gzip-compressed file."""

    def __init__(self, *args, **kwargs):
        pass


class BZ2ValidationError(Exception):
    """Raises exception if not valid bz2-compressed file."""

    def __init__(self, *args, **kwargs):
        pass


def register(opener_function):
    """Decorator that adds decorated opener function to the list of openers.

    :param opener_function: Opener function.
    :return: Opener function.
    """
    openers.append(opener_function)
    return opener_function


def filehandles(path, openers_list=openers, pattern='', verbose=False):
    """Main function that iterates over list of openers and decides which opener to use.

    :param str path: Path.
    :param list openers_list: List of openers.
    :param str pattern: Regular expression pattern.
    :param verbose: Print additional information.
    :type verbose: :py:obj:`True` or :py:obj:`False`
    :return: Filehandle(s).
    """
    if not verbose:
        logging.disable(logging.VERBOSE)

    for opener in openers_list:
        try:
            for filehandle in opener(path=path, pattern=pattern, verbose=verbose):
                with closing(filehandle):
                    yield filehandle
            break  # use the first successful opener function

        except (zipfile.BadZipfile, tarfile.ReadError, GZValidationError,
                BZ2ValidationError, IOError, NotADirectoryError):
             continue

        else:
            logger.verbose('No opener found for path: "{}"'.format(path))
            yield None


@register
def directory_opener(path, pattern='', verbose=False):
    """Directory opener.

    :param str path: Path.
    :param str pattern: Regular expression pattern.
    :return: Filehandle(s).
    """
    if not os.path.isdir(path):
        raise NotADirectoryError
    else:
        openers_list = [opener for opener in openers if not opener.__name__.startswith('directory')]  # remove directory

        for root, dirlist, filelist in os.walk(path):
            for filename in filelist:

                if pattern and not re.match(pattern, filename):
                    logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(filename), pattern))
                    continue

                filename_path = os.path.abspath(os.path.join(root, filename))
                for filehandle in filehandles(filename_path, openers_list=openers_list, pattern=pattern, verbose=verbose):
                    yield filehandle


@register
def ziparchive_opener(path, pattern='', verbose=False):
    """Opener that opens files from zip archive..

    :param str path: Path.
    :param str pattern: Regular expression pattern.
    :return: Filehandle(s).
    """
    with zipfile.ZipFile(io.BytesIO(urlopen(path).read()), 'r') if is_url(path) else zipfile.ZipFile(path, 'r') as ziparchive:
        for zipinfo in ziparchive.infolist():
            if not zipinfo.filename.endswith('/'):
                source = os.path.join(path, zipinfo.filename)

                if pattern and not re.match(pattern, zipinfo.filename):
                    logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(zipinfo.filename), pattern))
                    continue

                logger.verbose('Processing file: {}'.format(source))
                filehandle = ziparchive.open(zipinfo)
                yield filehandle


@register
def tararchive_opener(path, pattern='', verbose=False):
    """Opener that opens files from tar archive.

    :param str path: Path.
    :param str pattern: Regular expression pattern.
    :return: Filehandle(s).
    """
    with tarfile.open(fileobj=io.BytesIO(urlopen(path).read())) if is_url(path) else tarfile.open(path) as tararchive:
        for tarinfo in tararchive:
            if tarinfo.isfile():
                source = os.path.join(path, tarinfo.name)

                if pattern and not re.match(pattern, tarinfo.name):
                    logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(tarinfo.name), pattern))
                    continue

                logger.verbose('Processing file: {}'.format(source))
                filehandle = tararchive.extractfile(tarinfo)
                yield filehandle


@register
def gzip_opener(path, pattern='', verbose=False):
    """Opener that opens single gzip compressed file.

    :param str path: Path. 
    :param str pattern: Regular expression pattern. 
    :return: Filehandle(s).
    """
    source = path if is_url(path) else os.path.abspath(path)
    filename = os.path.basename(path)

    if pattern and not re.match(pattern, filename):
        logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(filename), pattern))
        return

    try:
        filehandle = gzip.GzipFile(fileobj=io.BytesIO(urlopen(path).read())) if is_url(path) else gzip.open(path)
        filehandle.read(1)
        filehandle.seek(0)
        logger.verbose('Processing file: {}'.format(source))
        yield filehandle
    except (OSError, IOError):
        raise GZValidationError


@register
def bz2_opener(path, pattern='', verbose=False):
    """Opener that opens single bz2 compressed file.

    :param str path: Path. 
    :param str pattern: Regular expression pattern.
    :return: Filehandle(s).
    """
    source = path if is_url(path) else os.path.abspath(path)
    filename = os.path.basename(path)

    if pattern and not re.match(pattern, filename):
        logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(path), pattern))
        return

    try:
        filehandle = bz2.open(io.BytesIO(urlopen(path).read())) if is_url(path) else bz2.open(path)
        filehandle.read(1)
        filehandle.seek(0)
        logger.verbose('Processing file: {}'.format(source))
        yield filehandle
    except (OSError, IOError):
        raise BZ2ValidationError


@register
def text_opener(path, pattern='', verbose=False):
    """Opener that opens single text file.

    :param str path: Path.
    :param str pattern: Regular expression pattern.
    :return: Filehandle(s).
    """
    source = path if is_url(path) else os.path.abspath(path)
    filename = os.path.basename(path)

    if pattern and not re.match(pattern, filename):
        logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(path), pattern))
        return

    filehandle = urlopen(path) if is_url(path) else open(path)
    logger.verbose('Processing file: {}'.format(source))
    yield filehandle


def is_url(path):
    """Test if path represents a valid URL string.

    :param str path: Path to file.
    :return: True if path is valid url string, False otherwise.
    :rtype: :py:obj:`True` or :py:obj:`False`
    """
    try:
        parse_result = urlparse(path)
        return all((parse_result.scheme, parse_result.netloc, parse_result.path))
    except ValueError:
        return False

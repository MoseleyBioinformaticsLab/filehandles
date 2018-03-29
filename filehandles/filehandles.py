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
import mimetypes
from contextlib import closing

import logging, verboselogs


if sys.version_info.major == 3:
    from urllib.request import urlopen
    from urllib.parse import urlparse
else:
    import bz2file as bz2
    from urllib2 import urlopen
    from urlparse import urlparse


# Set verbose logger
logger = verboselogs.VerboseLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.VERBOSE)


openers = []  # openers are added at the import time by @register decorator


def register(openercls):
    """Decorator that adds decorated class to the list of openers.

    :param openercls: Subclass of :class:`~filehandles.filehandles.Opener` that has `test()` and `open()` methods.
    :type openercls: Subclass of :class:`~filehandles.filehandles.Opener`.
    :return: Subclass of :class:`~filehandles.filehandles.Opener`.
    :rtype: :class:`~filehandles.filehandles.Opener`
    """
    openers.append(openercls)
    return openercls


def filehandles(path, openers_list=openers, pattern='', verbose=False, **extension_mimetype):
    """Main function that iterates over list of openers and decides which opener to use.

    :param str path: Path.
    :param list openers_list: List of openers.
    :param str pattern: Regular expression pattern.
    :param verbose: Print additional information.
    :type verbose: :py:obj:`True` or :py:obj:`False`
    :param extension_mimetype: Key-value pairs to specify non-standard mime types.
    :return: Filehandle(s).
    """
    if not verbose:
        logging.disable(logging.VERBOSE)

    for extension, mimetype in extension_mimetype.items():
        mimetypes.add_type(mimetype, '.{}'.format(extension))

    for openercls in openers_list:
        opener = openercls(**extension_mimetype)

        if opener.test(path):
            for filehandle in opener.open(path=path, pattern=pattern):
                with closing(filehandle):
                    yield filehandle
            break  # use the first opener that returned positive `opener.test()`


class Opener(object):
    """Abstract Opener class."""

    def __init__(self, **extension_mimetype):
        """Opener initializer.
        
        :param extension_mimetype: Key-value pairs to specify non-standard mime types.
        """
        for ext, mimetype in extension_mimetype.items():
            mimetypes.add_type(type=mimetype, ext=ext)

    @property
    def mimetypes(self):
        """Available mimetypes.
        
        :return: Tuple of mimetypes.
        :rtype: :py:class:`tuple`
        """
        return tuple(mimetypes.types_map.values())

    @property
    def extensions(self):
        """Available extensions.

        :return: Tuple of extensions.
        :rtype: :py:class:`tuple`
        """
        return tuple(mimetypes.types_map.keys())

    def open(self, path, pattern):
        """Abstract open method to be implemented in subclasses.
        
        :param str path: Path.
        :param str pattern: Regular expression pattern.
        :return: Filehandle(s).
        """
        raise NotImplementedError('Subclass must implement specific "open()" method')

    @classmethod
    def test(cls, path):
        """Abstract test method to be implemented in subclasses.
        
        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        raise NotImplementedError('Subclass must implement specific "test()" method')


@register
class Directory(Opener):
    """Opener that opens files from directory."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.
        
        :param str path: Path.
        :param str pattern: Regular expression pattern.
        :return: Filehandle(s).
        """
        for root, dirlist, filelist in os.walk(path):
            for filename in filelist:
                mimetype, encoding = mimetypes.guess_type(filename)

                if mimetype in ('application/x-tar', 'application/zip') or encoding in ('gzip', 'bzip2'):
                    logger.verbose('Skipping compressed file: {}'.format(os.path.abspath(filename)))
                    continue

                if mimetype in self.mimetypes:
                    if pattern and not re.match(pattern, filename):
                        logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(filename), pattern))
                        continue

                    logger.verbose('Processing file: {}'.format(os.path.abspath(filename)))
                    with open(os.path.join(root, filename)) as filehandle:
                        yield filehandle
                else:
                    logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(os.path.abspath(filename), mimetype))
                    continue

    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.
        
        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        if os.path.isdir(path):
            return True
        return False


@register
class ZipArchive(Opener):
    """Opener that opens files from zip archive."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :param str pattern: Regular expression pattern.
        :return: Filehandle(s).
        """
        with zipfile.ZipFile(io.BytesIO(urlopen(path).read()), 'r') if is_url(path) else zipfile.ZipFile(path, 'r') as ziparchive:
            for zipinfo in ziparchive.infolist():
                if not zipinfo.filename.endswith('/'):
                    mimetype, encoding = mimetypes.guess_type(zipinfo.filename)
                    source = os.path.join(path, zipinfo.filename)

                    if mimetype in self.mimetypes:
                        if pattern and not re.match(pattern, zipinfo.filename):
                            logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(zipinfo.filename), pattern))
                            continue

                        logger.verbose('Processing file: {}'.format(source))
                        filehandle = ziparchive.open(zipinfo)
                        yield filehandle
                    else:
                        logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(source, mimetype))
                        continue


    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.

        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype == 'application/zip':
            return True
        return False


@register
class TarArchive(Opener):
    """Opener that opens files from tar archive."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.

        :param str path: Path.
        :param str pattern: Regular expression pattern.
        :return: Filehandle(s).
        """
        with tarfile.open(fileobj=io.BytesIO(urlopen(path).read())) if is_url(path) else tarfile.open(path) as tararchive:
            for tarinfo in tararchive:
                if tarinfo.isfile():
                    mimetype, encoding = mimetypes.guess_type(tarinfo.name)
                    source = os.path.join(path, tarinfo.name)

                    if mimetype in self.mimetypes:
                        if pattern and not re.match(pattern, tarinfo.name):
                            logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(tarinfo.name), pattern))
                            continue

                        logger.verbose('Processing file: {}'.format(source))
                        filehandle = tararchive.extractfile(tarinfo)
                        yield filehandle
                    else:
                        logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(source, mimetype))
                        continue


    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.

        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype == 'application/x-tar':
            return True
        return False


@register
class SingleBZ2CompressedTextFile(Opener):
    """Opener that opens single compressed file."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param str pattern: Regular expression pattern.
        :return: Filehandle(s).
        """
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)
        filename = os.path.basename(path)

        if mimetype in self.mimetypes:
            if pattern and not re.match(pattern, filename):
                logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(path), pattern))
                return

            logger.verbose('Processing file: {}'.format(source))
            with bz2.open(urlopen(path)) if is_url(path) else bz2.open(path) as filehandle:
                yield filehandle
        else:
            logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(source, mimetype))

    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.

        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        _, encoding = mimetypes.guess_type(path)
        if encoding == 'bzip2':
            return True
        return False


@register
class SingleGzipCompressedTextFile(Opener):
    """Opener that opens single compressed file."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param str pattern: Regular expression pattern. 
        :return: Filehandle(s).
        """
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)
        filename = os.path.basename(path)

        if mimetype in self.mimetypes:
            if pattern and not re.match(pattern, filename):
                logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(filename), pattern))
                return

            logger.verbose('Processing file: {}'.format(source))
            with gzip.GzipFile(fileobj=io.BytesIO(urlopen(path).read())) if is_url(path) else gzip.open(path) as filehandle:
                yield filehandle
        else:
            logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(source, mimetype))

    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.

        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        _, encoding = mimetypes.guess_type(path)
        if encoding == 'gzip':
            return True
        return False


@register
class SingleTextFileWithNoExtension(Opener):
    """Opener that opens single file."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param str pattern: Regular expression pattern. 
        :return: Filehandle(s).
        """
        source = path if is_url(path) else os.path.abspath(path)
        filename = os.path.basename(path)

        if pattern and not re.match(pattern, filename):
            logger.verbose('Skipping file: {}, did not match regex pattern "{}"'.format(os.path.abspath(filename), pattern))
            return

        logger.verbose('Processing file: {}'.format(source))
        filehandle = urlopen(path) if is_url(path) else open(path)
        yield filehandle

    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.

        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype is None and encoding is None:
            return True
        return False


@register
class SingleTextFile(Opener):
    """Opener that opens single file."""

    def open(self, path, pattern):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param str pattern: Regular expression pattern.  
        :return: Filehandle(s).
        """
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)
        filename = os.path.basename(path)

        if mimetype not in self.mimetypes:
            if pattern and not re.match(pattern, filename):
                logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(source, mimetype))
                return

            logger.verbose('Processing file: {}'.format(source))
            filehandle = urlopen(path) if is_url(path) else open(path)
            yield filehandle
        else:
            logger.verbose('Skipping file: {}, mimetype "{}" is not defined'.format(source, mimetype))

    @classmethod
    def test(cls, path):
        """Concrete implementation of `test()` method.

        :param str path: Path. 
        :return: True if opener can be used, False otherwise.
        :rtype: :py:obj:`True` or :py:obj:`False`
        """
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype.startswith('text/'):
            return True
        return False


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

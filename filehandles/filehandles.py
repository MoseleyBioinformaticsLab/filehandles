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
import zipfile
import tarfile
import bz2
import gzip
import mimetypes
from contextlib import closing


if sys.version_info.major == 3:
    from urllib.request import urlopen
    from urllib.parse import urlparse
else:
    import bz2file as bz2
    from urllib2 import urlopen
    from urlparse import urlparse


openers = []  # openers are added at the import time by register decorator


def register(openercls):
    """Decorator that adds decorated class to the list of openers.

    :param openercls: Subclass of :class:`~filehandles.filehandles.Opener` that has `test()` and `open()` methods.
    :type openercls: Subclass of :class:`~filehandles.filehandles.Opener`.
    :return: Subclass of :class:`~filehandles.filehandles.Opener`.
    :rtype: :class:`~filehandles.filehandles.Opener`
    """
    openers.append(openercls)
    return openercls


def filehandles(path, openers_list=openers, verbose=False, **extension_mimetype):
    """Main function that iterates over list of openers and decides which opener to use.

    :param str path: Path.
    :param list openers_list: List of openers.
    :param verbose: Print additional information.
    :type verbose: :py:obj:`True` or :py:obj:`False`
    :param extension_mimetype: Key-value pairs to specify non-standard mime types.
    :return: Filehandle(s).
    """
    for extension, mimetype in extension_mimetype.items():
        mimetypes.add_type(mimetype, '.{}'.format(extension))

    for openercls in openers_list:
        opener = openercls(**extension_mimetype)

        if opener.test(path):
            for fh in opener.open(path=path, verbose=verbose):
                with closing(fh):
                    yield fh
            break  # use the first opener that returned positive `opener.test()`


class Opener(object):
    """Abstract Opener class."""

    def __init__(self, **extension_mimetype):
        """Opener initializer.
        
        :param extension_mimetype: Key-value pairs to specify non-standard mime types.
        """
        self.extensions = tuple(extension_mimetype.keys())
        self.mimetypes = tuple(extension_mimetype.values())

    def open(self, path, verbose=False):
        """Abstract open method to be implemented in subclasses.
        
        :param str path: Path.
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.
        
        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        for root, dirlist, filelist in os.walk(path):
            for fname in filelist:
                mimetype, encoding = mimetypes.guess_type(fname)

                if mimetype not in self.mimetypes:
                    if verbose:
                        print('Skipping file: "{}"'.format(os.path.abspath(fname)))
                    continue
                else:
                    if verbose:
                        print('Processing file: "{}"'.format(os.path.abspath(fname)))

                    with open(os.path.join(root, fname)) as filehandle:
                        yield filehandle

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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        with zipfile.ZipFile(io.BytesIO(urlopen(path).read()), "r") if is_url(path) else zipfile.ZipFile(path, "r") as ziparchive:
            for zipinfo in ziparchive.infolist():
                if not zipinfo.filename.endswith('/'):
                    mimetype, encoding = mimetypes.guess_type(zipinfo.filename)
                    source = os.path.join(path, zipinfo.filename)

                    if mimetype not in self.mimetypes:
                        if verbose:
                            print('Skipping file: {}'.format(source))
                        continue
                    else:
                        if verbose:
                            print('Processing file: {}'.format(source))

                        filehandle = ziparchive.open(zipinfo)
                        yield filehandle

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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        with tarfile.open(fileobj=io.BytesIO(urlopen(path).read())) if is_url(path) else tarfile.open(path) as tararchive:
            for tarinfo in tararchive:
                if tarinfo.isfile():
                    mimetype, encoding = mimetypes.guess_type(tarinfo.name)
                    source = os.path.join(path, tarinfo.name)

                    if mimetype not in self.mimetypes:
                        if verbose:
                            print('Skipping file: {}'.format(source))
                        continue
                    else:
                        if verbose:
                            print('Processing file: {}'.format(source))

                    filehandle = tararchive.extractfile(tarinfo)
                    yield filehandle

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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)

        with bz2.open(urlopen(path)) if is_url(path) else bz2.open(path) as filehandle:
            if mimetype not in self.mimetypes:
                if verbose:
                    print('Skipping file: {}'.format(source))
                pass
            else:
                if verbose:
                    print('Processing file: {}'.format(source))
                yield filehandle

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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)

        with gzip.GzipFile(fileobj=io.BytesIO(urlopen(path).read())) if is_url(path) else gzip.open(path) as filehandle:
            if mimetype not in self.mimetypes:
                if verbose:
                    print('Skipping file: {}'.format(source))
                pass
            else:
                if verbose:
                    print('Processing file: {}'.format(source))
                yield filehandle

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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        source = path if is_url(path) else os.path.abspath(path)

        if verbose:
            print('Processing file: {}'.format(source))

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

    def open(self, path, verbose=False):
        """Concrete implementation of `open()` method.

        :param str path: Path. 
        :param verbose: Print additional information.
        :type verbose: :py:obj:`True` or :py:obj:`False` 
        :return: Filehandle(s).
        """
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)

        if mimetype not in self.mimetypes:
            if verbose:
                print('Skipping file: {}'.format(source))
            pass
        else:
            if verbose:
                print('Processing file: {}'.format(source))

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

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

import os
import io
import sys
import zipfile
import tarfile
import bz2
import gzip
import lzma
import mimetypes
from contextlib import closing

if sys.version_info.major == 3:
    from urllib.request import urlopen
    from urllib.parse import urlparse
    from urllib.parse import urljoin
    from urllib.error import HTTPError
else:
    from urllib2 import urlopen
    from urlparse import urlparse
    from urlparse import urljoin
    from urllib2 import HTTPError


openers = []


def register(openercls):
    """

    :param openercls:
    :return:
    """
    openers.append(openercls)
    return openercls


def filehandles(path, openers_list=openers, verbose=False, **extension_mimetype):
    """

    :param path:
    :param openers_list:
    :param verbose:
    :param extension_mimetype:
    :return:
    """
    for extension, mimetype in extension_mimetype.items():
        mimetypes.add_type(mimetype, '.{}'.format(extension))

    for openercls in openers_list:
        opener = openercls(**extension_mimetype)

        if opener.test(path):

            print(opener.__class__.__name__)

            for fh in opener.open(path=path, verbose=verbose):
                with closing(fh):
                    yield fh
            break  # use the first opener that returned positive opener.test()


class Opener(object):

    def __init__(self, **extension_mimetype):
        self.extensions = tuple(extension_mimetype.keys())
        self.mimetypes = tuple(extension_mimetype.values())

    def open(self, path, verbose=False):
        raise NotImplementedError('Subclass must implement specific "open()" method')

    @classmethod
    def test(cls, path):
        raise NotImplementedError('Subclass must implement specific "test()" method')


@register
class Directory(Opener):

    def open(self, path, verbose=False):
        for root, dirlist, filelist in os.walk(path):
            for fname in filelist:
                mimetype, encoding = mimetypes.guess_type(fname)

                if mimetype not in self.mimetypes:
                    if verbose:
                        print('Skipping file: {}'.format(os.path.abspath(fname)))
                    continue
                else:
                    if verbose:
                        print('Processing file: {}'.format(os.path.abspath(fname)))

                    with open(os.path.join(root, fname)) as filehandle:
                        yield filehandle

    @classmethod
    def test(cls, path):
        if os.path.isdir(path):
            return True
        return False


@register
class ZipArchive(Opener):

    def open(self, path, verbose=False):
        with zipfile.ZipFile(io.BytesIO(urlopen(path).read()), "r") if is_url(path) else zipfile.ZipFile(path) as ziparchive:
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
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype == 'application/zip':
            return True
        return False


@register
class TarArchive(Opener):

    def open(self, path, verbose=False):
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
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype == 'application/x-tar':
            return True
        return False


@register
class SingleCompressedTextFile(Opener):

    opener = {
        'bzip2': bz2.open,
        'gzip': gzip.open,
        'xz': lzma.open
    }

    def open(self, path, verbose=False):
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)
        open = self.opener[encoding]

        with open(io.BytesIO(urlopen(path).read())) if is_url(path) else open(path) as filehandle:
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
        _, encoding = mimetypes.guess_type(path)
        if encoding in cls.opener.keys():
            return True
        return False


@register
class SingleTextFileWithNoExtension(Opener):

    def open(self, path, verbose=False):
        source = path if is_url(path) else os.path.abspath(path)

        if verbose:
            print('Processing file: {}'.format(source))

        with urlopen(path) if is_url(path) else open(path) as filehandle:
            yield filehandle

    @classmethod
    def test(cls, path):
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype is None and encoding is None:
            return True
        return False


@register
class SingleTextFile(Opener):

    def open(self, path, verbose=False):
        mimetype, encoding = mimetypes.guess_type(path)
        source = path if is_url(path) else os.path.abspath(path)

        if mimetype not in self.mimetypes:
            if verbose:
                print('Skipping file: {}'.format(source))
            pass
        else:
            if verbose:
                print('Processing file: {}'.format(source))

            with urlopen(path) if is_url(path) else open(path) as filehandle:
                yield filehandle

    @classmethod
    def test(cls, path):
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


if __name__ == "__main__":

    from pprint import pprint

    script = sys.argv.pop(0)
    source = sys.argv.pop(0)

    print("openers:", openers)

    # Test class
    class Mock(object):

        def __init__(self, fh):
            self.fh = fh
            self.content = fh.read()

    # Example usage
    def read_files(*sources):
        for source in sources:
            for fh in filehandles(source, verbose=True, cif='text/cif', str='text/nmrstar'):
                yield Mock(fh)

    g = read_files(source)

    for i in g:
        print(i)

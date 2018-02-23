#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import filehandles


class Mock(object):
    """Test object that accepts file handle."""

    def __init__(self, fh):
        self.fh = fh
        self.first_line  = fh.readline()


@pytest.mark.parametrize('files_source', [
    'tests/example_data/2rpv.cif',
    'tests/example_data/2rpv',
    'tests/example_data/2rpv.cif.gz',
    'tests/example_data/2rpv.cif.bz2',
    'tests/example_data/directory',
    'tests/example_data/archive.zip',
    'tests/example_data/archive.tar.gz',
    'tests/example_data/archive.tar.bz2',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/2rpv.cif',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/2rpv',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/2rpv.cif.gz',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/2rpv.cif.bz2',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/archive.zip',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/archive.tar.gz',
    'https://raw.githubusercontent.com/MoseleyBioinformaticsLab/filehandles/master/tests/example_data/archive.tar.bz2'
])
def test_reading(files_source):
    for fh in filehandles.filehandles(files_source, cif='text/cif'):
        mock = Mock(fh)
        assert mock.first_line.strip() in ('data_2RPV', b'data_2RPV')

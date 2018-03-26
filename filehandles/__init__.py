#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from .filehandles import filehandles


__version__ = "0.1.0"

# Setting default logging handler
try:  # Python 2/3 compatibility code
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

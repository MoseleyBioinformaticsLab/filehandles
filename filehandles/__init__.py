#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from .filehandles import filehandles


__version__ = "0.3.1.post1"


try:  # Python 2/3 compatibility code
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass


# Setting default logging handler
logging.getLogger(__name__).addHandler(NullHandler())

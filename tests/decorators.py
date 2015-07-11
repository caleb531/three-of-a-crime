#!/usr/bin/env python3

import sys
from functools import wraps
from io import StringIO


def redirect_stdout(fn):
    """temporarily redirect stdout to new output stream"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        original_stdout = sys.stdout
        out = StringIO()
        try:
            sys.stdout = out
            return fn(out, *args, **kwargs)
        finally:
            sys.stdout = original_stdout
    return wrapper

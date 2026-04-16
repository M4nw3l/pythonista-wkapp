"""Tests for WKApp.static_file route behaviour.

Run with either::

    python test/test_static_file.py

or, from inside the test directory::

    pytest test_static_file.py
"""
import os
import sys
import tempfile
import types
import unittest

# Ensure repo root is on sys.path so `import wkapp` works when this file is
# executed directly (``python test/test_static_file.py``).
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# wkapp.py depends on the Pythonista-only `ui` module and on wkwebview, which
# in turn imports `objc_util`. Neither is available on regular CPython, so
# stub them here before importing wkapp so the tests can run in any
# environment.
if 'ui' not in sys.modules:
    _ui = types.ModuleType('ui')

    class _UIView:
        def __init__(self, *args, **kwargs):
            pass

    _ui.View = _UIView
    _ui.load_view = lambda *args, **kwargs: None
    sys.modules['ui'] = _ui

if 'wkwebview' not in sys.modules:
    import functools as _functools
    import json as _json
    import re as _re

    _wkwebview = types.ModuleType('wkwebview')

    class _WKWebView:
        def __init__(self, *args, **kwargs):
            pass

    _wkwebview.WKWebView = _WKWebView
    # wkapp.py relies on ``from wkwebview import *`` to transitively pull in
    # the standard library modules that wkwebview itself imports. Expose the
    # ones referenced at wkapp module load time so import order matches
    # Pythonista.
    _wkwebview.functools = _functools
    _wkwebview.json = _json
    _wkwebview.re = _re
    sys.modules['wkwebview'] = _wkwebview

from bottle import HTTPError  # noqa: E402

import wkapp  # noqa: E402


class StaticFileTests(unittest.TestCase):
    """Ensure the static_file handler aborts with 404 for missing files."""

    def test_static_file_nonexistent_returns_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = wkapp.WKApp(tmp)
            with self.assertRaises(HTTPError) as ctx:
                app.static_file('this_file_does_not_exist.txt')
            self.assertEqual(ctx.exception.status_code, 404)


if __name__ == '__main__':
    unittest.main()

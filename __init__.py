''' 
WKApp - A modern HTML5 UI framework for building iOS apps with Pythonista 3 and WebKit

https://github.com/M4nw3l/pythonista-wkapp
'''
__version__ = '0.0.1'

try:
    from .wkwebview import *
    from .wkapp import *
except:
    pass
  
# mostly convenience includes for bottle
# besides its implementation specific includes for the mako templating integration
from bottle import (
    request,
    response,
    route,
    static_file,
)


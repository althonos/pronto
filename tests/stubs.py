# coding: utf-8
import threading
import os

try:
    from http.server import HTTPServer
    from http.server import SimpleHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler

class StubHTTPServer(threading.Thread):
    daemon = True

    class _RequestHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            return self._datadir + path
        def log_message(self, format, *args):
            pass

    def __init__(self, datadir):
        super(StubHTTPServer, self).__init__()
        self._RequestHandler._datadir = datadir
        self.server = HTTPServer(("localhost", 8080), self._RequestHandler)

    def run(self):
        self.server.serve_forever()

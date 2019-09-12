# coding: utf-8

import http.server
import os
import threading


class StubHTTPServer(threading.Thread):
    daemon = True

    class _RequestHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            return self._datadir + path
        def log_message(self, format, *args):
            pass

    def __init__(self, datadir):
        super(StubHTTPServer, self).__init__()
        self._RequestHandler._datadir = datadir
        self.domain, self.port = address = "localhost", 8080
        self.server = http.server.HTTPServer(address, self._RequestHandler)

    def run(self):
        self.server.serve_forever()

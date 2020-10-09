#!/usr/bin/env python

import os
import http.server as server
from pathlib import Path, PurePosixPath


class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def do_POST(self):
        filename = Path(os.path.basename(self.path))
        file_length = int(self.headers['Content-Length'])
        with open(PurePosixPath('/tmp').joinpath(filename.name), 'wb') as output_file:
            output_file.write(self.rfile.read(file_length))
        self.send_response(201, 'Created')
        self.end_headers()
        reply_body = 'Saved "%s"\n' % filename.with_suffix('')
        self.wfile.write(reply_body.encode('utf-8'))


if __name__ == '__main__':
    server.test(HandlerClass=HTTPRequestHandler)

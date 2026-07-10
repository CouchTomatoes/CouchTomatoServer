#!/usr/bin/python

####
# 06/2010 Nic Wolfe <nic@wolfeden.ca>
# 02/2006 Will Holcomb <wholcomb@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#

import urllib.request, urllib.error, urllib.parse
import mimetypes
import os, sys, uuid

# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1

def _to_bytes(value):
    return value.encode('utf-8') if isinstance(value, str) else value

class MultipartPostHandler(urllib.request.BaseHandler):
    handler_order = urllib.request.HTTPHandler.handler_order - 10 # needs to run first

    def http_request(self, request):
        data = request.data
        if data is not None and not isinstance(data, (str, bytes)):
            v_files = []
            v_vars = []
            try:
                for(key, value) in list(data.items()):
                    if isinstance(value, (list, tuple)) or hasattr(value, 'read'):
                        v_files.append((key, value))
                    else:
                        v_vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise TypeError("not a valid non-string sequence or mapping object").with_traceback(traceback)

            if len(v_files) == 0:
                data = urllib.parse.urlencode(v_vars, doseq)
            else:
                boundary, data = MultipartPostHandler.multipart_encode(v_vars, v_files)
                contenttype = 'multipart/form-data; boundary=%s' % boundary
                if(request.has_header('Content-Type')
                   and request.get_header('Content-Type').find('multipart/form-data') != 0):
                    print(("Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')))
                request.add_unredirected_header('Content-Type', contenttype)

            request.data = data
        return request

    @staticmethod
    def multipart_encode(vars, files, boundary = None, buffer = None):
        if boundary is None:
            boundary = uuid.uuid4().hex
        if buffer is None:
            buffer = b''
        boundary_bytes = boundary.encode('ascii')
        for(key, value) in vars:
            buffer += b'--%s\r\n' % boundary_bytes
            buffer += b'Content-Disposition: form-data; name="%s"' % _to_bytes(key)
            buffer += b'\r\n\r\n' + _to_bytes(value) + b'\r\n'
        for(key, fd) in files:

            # allow them to pass in a file-like object or a tuple with name & data
            if hasattr(fd, 'read'):
                name_in = fd.name
                fd.seek(0)
                data_in = fd.read()
            elif isinstance(fd, (tuple, list)):
                name_in, data_in = fd

            filename = os.path.basename(_to_bytes(name_in)).decode('utf-8', 'replace')
            contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            buffer += b'--%s\r\n' % boundary_bytes
            buffer += b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (_to_bytes(key), _to_bytes(filename))
            buffer += b'Content-Type: %s\r\n' % _to_bytes(contenttype)
            # buffer += 'Content-Length: %s\r\n' % file_size
            try:
                buffer += b'\r\n' + _to_bytes(data_in) + b'\r\n'
            except Exception as e:
                raise e
        buffer += b'--%s--\r\n\r\n' % boundary_bytes
        return boundary, buffer

    https_request = http_request

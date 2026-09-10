#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build once and preview on loopback. Restart after editing source files."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from build import ROOT, build, load_config

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8780)
    parser.add_argument('--no-build',action='store_true')
    args=parser.parse_args()
    if not args.no_build:build()
    base=load_config(ROOT)['base_path']
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if base:
                if urlsplit(self.path).path==base:
                    self.send_response(301);self.send_header('Location',base+'/');self.end_headers();return
                if not self.path.startswith(base+'/'):
                    self.send_error(404);return
                self.path=self.path[len(base):]
            super().do_GET()
        def end_headers(self):
            self.send_header('Cache-Control','no-store')
            super().end_headers()
    handler=functools.partial(Handler,directory=str(ROOT/'dist'))
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler)
    print(f'预览：http://127.0.0.1:{args.port}{base}/',flush=True)
    print('修改文章后重新执行 python3 build.py，再刷新页面。',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()

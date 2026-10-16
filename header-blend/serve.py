"""Serve this folder locally: python3 serve.py  ->  http://localhost:8000

index.html is written for the claude.ai artifact host, which wraps it in <!doctype html> and a
viewport meta. This server adds the same wrapper so the page renders in standards mode locally.
"""
import http.server, os

HERE = os.path.dirname(os.path.abspath(__file__))
WRAP = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            body = (WRAP + open(os.path.join(HERE, "index.html"), encoding="utf-8").read() + "</body></html>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

if __name__ == "__main__":
    print("Serving on http://localhost:8000")
    http.server.ThreadingHTTPServer(("", 8000), Handler).serve_forever()

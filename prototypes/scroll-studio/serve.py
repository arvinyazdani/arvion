"""Loopback-only, allowlisted prototype server. No Django, DB or customer writes."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
FILES = {"/": (ROOT / "index.html", "text/html"), "/index.html": (ROOT / "index.html", "text/html")}
for name, mime in (("studio.css", "text/css"), ("studio.mjs", "text/javascript"), ("model.mjs", "text/javascript")):
    FILES["/" + name] = (ROOT / name, mime)
for name, mime in (("film.html", "text/html"), ("film.css", "text/css"), ("film.mjs", "text/javascript"), ("film-model.mjs", "text/javascript")):
    FILES["/" + name] = (ROOT / name, mime)
FILES["/assets/css/tokens.css"] = (REPO / "core/static/core/css/tokens.css", "text/css")
for name, mime in (("journey.html", "text/html"), ("journey.css", "text/css"), ("journey.mjs", "text/javascript"), ("journey-model.mjs", "text/javascript")):
    FILES["/" + name] = (ROOT / name, mime)
for weight in ("Regular", "Bold", "Black"):
    name = "Vazirmatn-" + weight + ".woff2"
    FILES["/assets/fonts/" + name] = (REPO / "core/static/core/fonts" / name, "font/woff2")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        entry = FILES.get(urlsplit(self.path).path)
        if entry is None:
            self.send_error(404)
            return
        body = entry[0].read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", entry[1] + ("; charset=utf-8" if entry[1].startswith("text/") else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.send_error(405)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8160)
    args = parser.parse_args()
    print("Review prototype: http://127.0.0.1:%s/" % args.port, flush=True)
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()

"""Exercise the real Nginx cache config against a disposable, loopback-only backend.

Run as an unprivileged operator with Python 3 and Nginx installed. Never uses
Django, production data, credentials, or the running Nginx configuration.
"""
import argparse
import http.client
import http.server
import pathlib
import shutil
import socket
import subprocess
import tempfile
import threading
import time


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(pathlib.Path(__file__).with_name('nginx.conf')))
    parser.add_argument('--nginx', default=shutil.which('nginx'))
    args = parser.parse_args()
    if not args.nginx:
        parser.error('nginx must be installed; no package is installed by this test')
    source = pathlib.Path(args.config).read_text()
    maps, servers = source.split('server {', 1)
    first_server = servers.split('\nserver {', 1)[0]
    location = first_server.split('    location / {', 1)[1].split('\n    }', 1)[0]
    second_location = source.rsplit('    location / {', 1)[1].split('\n    }', 1)[0]
    assert location == second_location, 'HTTP/HTTPS proxy cache gates differ'
    mode = {'cache_control': 'public, max-age=0, s-maxage=60', 'status': 200, 'cookie': False}
    hits = {'count': 0}

    class Backend(http.server.BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass

        def do_GET(self):
            hits['count'] += 1
            private = self.path.split('?', 1)[0] in ('/fa/start/', '/fa/contact/', '/fa/account/login/')
            body = ('public sample ' + str(hits['count'])).encode()
            self.send_response(mode['status'])
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'private, no-store' if private else mode['cache_control'])
            self.send_header('Vary', 'Cookie')
            if mode['cookie'] or private:
                self.send_header('Set-Cookie', 'csrftoken=test-' + str(hits['count']) + '; Path=/')
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        do_HEAD = do_GET
        do_POST = do_GET

    backend = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Backend)
    thread = threading.Thread(target=backend.serve_forever, daemon=True)
    thread.start()
    with tempfile.TemporaryDirectory(prefix='rvion-nginx-cache-test-') as tmp:
        root = pathlib.Path(tmp)
        port = free_port()
        maps = maps.replace('/var/cache/nginx/rvion-public', str(root / 'cache'))
        location = location.replace('http://127.0.0.1:8000', 'http://127.0.0.1:' + str(backend.server_port))
        config = root / 'nginx.conf'
        config.write_text('daemon off;\nmaster_process off;\npid ' + str(root / 'nginx.pid')
                         + ';\nerror_log ' + str(root / 'error.log') + ';\nevents {}\nhttp {\n'
                         + 'access_log off;\n' + maps + '\nserver { listen 127.0.0.1:' + str(port)
                         + '; server_name rvionai.com; location / {\n' + location + '\n}\n}\n}\n')
        subprocess.run([args.nginx, '-t', '-p', tmp, '-c', str(config)], check=True)
        nginx = subprocess.Popen([args.nginx, '-p', tmp, '-c', str(config)], stdout=subprocess.DEVNULL)
        try:
            for unused in range(100):
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.1):
                        break
                except OSError:
                    if nginx.poll() is not None:
                        raise RuntimeError((root / 'error.log').read_text())
                    time.sleep(.02)

            def request(path, headers=None, method='GET'):
                conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                conn.request(method, path, headers={'Host': 'rvionai.com', **(headers or {})})
                response = conn.getresponse()
                result = (response.status, response.getheader('X-Rvion-Origin-Cache'), response.read(), response.getheader('Set-Cookie'))
                conn.close()
                return result

            checks = 0
            for path in ('/fa/', '/en/', '/fa/about/', '/en/services/', '/fa/services/custom-web-application/',
                         '/en/blog/', '/fa/blog/example/', '/en/tools/cost-calculator/', '/fa/privacy/'):
                first, second = request(path), request(path)
                assert first[1] == 'MISS' and second[1] == 'HIT', (path, first, second)
                assert first[2] == second[2] and not second[3], path
                assert request(path, method='HEAD')[1] == 'HIT', path
                for headers in ({'Cookie': 'sessionid=test'}, {'Cookie': 'messages=test'}, {'Authorization': 'Bearer test'}):
                    assert request(path, headers)[1] == 'BYPASS', path
                assert request(path + '?probe=1')[1] == 'BYPASS', path
                assert request(path, method='POST')[1] == 'BYPASS', path
                checks += 8
            for path in ('/fa/contact/', '/fa/start/', '/fa/account/login/', '/fa/account/dashboard/',
                         '/fa/management/', '/admin/', '/fa/assessments/', '/fa/assessments/example/',
                         '/fa/assessments/attempt/test/', '/fa/assessments/order/test/',
                         '/fa/projects/demos/', '/fa/projects/demos/example/', '/health/', '/robots.txt'):
                assert request(path)[1] == request(path)[1] == 'BYPASS', path
                checks += 2
            assert request('/en/company/', {'Host': 'other.example'})[1] == 'BYPASS'
            checks += 1
            for control in ('private, no-store', 'public, no-store', 'no-cache', 'max-age=60'):
                mode['cache_control'] = control
                assert request('/fa/company/')[1] == request('/fa/company/')[1] == 'MISS', control
                checks += 2
            mode['cache_control'] = 'public, s-maxage=60'
            mode['cookie'] = True
            assert request('/fa/refund-policy/')[1] == request('/fa/refund-policy/')[1] == 'MISS'
            checks += 2
            mode['cookie'] = False
            for status in (302, 404, 500):
                mode['status'] = status
                assert request('/en/refund-policy/')[1] == request('/en/refund-policy/')[1] == 'MISS', status
                checks += 2
            mode['status'] = 200
            mode['cache_control'] = 'public, max-age=0, s-maxage=1'
            first = request('/en/service-terms/')
            assert first[1] == 'MISS'
            assert request('/en/service-terms/')[1] == 'HIT'
            time.sleep(2.1)
            expired = request('/en/service-terms/')
            assert expired[1] == 'EXPIRED' and expired[2] != first[2]
            checks += 3
            print('PASS:', checks, 'real Nginx cache checks; no production DB used')
        finally:
            nginx.terminate()
            nginx.wait(timeout=10)
            backend.shutdown()
            backend.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    main()

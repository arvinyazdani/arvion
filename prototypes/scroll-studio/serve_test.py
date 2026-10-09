"""Prototype HTTP boundary tests; no application database or production access."""
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from serve import Handler


class PrototypeServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%s" % cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_document_is_noindex_and_has_no_external_submit(self):
        with urlopen(self.base + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
            self.assertIn("connect-src 'none'", response.headers["Content-Security-Policy"])
            self.assertIn("form-action 'none'", response.headers["Content-Security-Policy"])
            body = response.read().decode()
            self.assertEqual(body.count("<h1 "), 1)
            self.assertNotIn("<form", body)

    def test_modules_have_correct_mime(self):
        for path in ("/model.mjs", "/studio.mjs", "/film.mjs", "/film-model.mjs", "/journey.mjs", "/journey-model.mjs"):
            with urlopen(self.base + path) as response:
                self.assertTrue(response.headers["Content-Type"].startswith("text/javascript"))

    def test_coded_film_is_not_a_video_or_remote_embed(self):
        with urlopen(self.base + "/film.html") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
            body = response.read().decode()
            self.assertIn('id="scene"', body)
            self.assertIn('type="range"', body)
            self.assertNotIn("<video", body)
            self.assertNotIn("<iframe", body)
            self.assertNotIn("https://", body)
        with urlopen(self.base + "/film.css") as response:
            self.assertTrue(response.headers["Content-Type"].startswith("text/css"))

    def test_branching_journey_is_local_only(self):
        with urlopen(self.base + "/journey.html") as response:
            body = response.read().decode()
            self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
            self.assertIn('id="choices"', body)
            self.assertIn('id="skip"', body)
            self.assertNotIn("<video", body)
            self.assertNotIn("<form", body)
            self.assertNotIn("https://", body)
        with urlopen(self.base + "/journey.css") as response:
            self.assertTrue(response.headers["Content-Type"].startswith("text/css"))

    def test_local_font_and_canonical_tokens_exist(self):
        for path in ("/assets/fonts/Vazirmatn-Regular.woff2", "/assets/fonts/Vazirmatn-Bold.woff2", "/assets/css/tokens.css"):
            with urlopen(self.base + path) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(response.read())

    def test_repo_secrets_and_parent_paths_not_served(self):
        for path in ("/.env", "/serve.py", "/../../.server-secrets.txt", "/%2e%2e/.env", "/assets/../.env"):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.base + path)
            self.assertEqual(error.exception.code, 404)

    def test_post_is_rejected(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/", data=b"test", method="POST"))
        self.assertEqual(error.exception.code, 405)


if __name__ == "__main__":
    unittest.main()

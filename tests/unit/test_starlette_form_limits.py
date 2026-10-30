"""Tiny synthetic HTTP regressions for the real Starlette form parser.

The module can run directly for a framework-only diagnostic without importing
the financial application or its database fixtures.
"""

import unittest

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient


async def _bounded_form(request: Request):
    async with request.form(max_fields=2, max_part_size=4) as form:
        return JSONResponse({"fields": list(form.multi_items())})


class TestStarletteFormLimits(unittest.TestCase):
    def setUp(self):
        app = Starlette(routes=[Route("/form", _bounded_form, methods=["POST"])])
        self.client = self.enterContext(TestClient(app, raise_server_exceptions=False))

    def request_form(self, pairs, media_type):
        if media_type == "urlencoded":
            body = "&".join(f"{name}={value}" for name, value in pairs).encode("ascii")
            content_type = "application/x-www-form-urlencoded"
        else:
            body = b"".join(
                b'--safe\r\nContent-Disposition: form-data; name="' + name.encode("ascii")
                + b'"\r\n\r\n' + value.encode("ascii") + b"\r\n"
                for name, value in pairs
            ) + b"--safe--\r\n"
            content_type = "multipart/form-data; boundary=safe"
        self.assertLess(len(body), 512)
        return self.client.post("/form", content=body, headers={"Content-Type": content_type})

    def assert_rejected(self, response):
        self.assertEqual(response.status_code, 400)
        for internal in ("Traceback", "site-packages", "AssertionError"):
            self.assertNotIn(internal, response.text)

    def assert_valid(self, response, pairs):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"fields": [list(pair) for pair in pairs]})

    def test_urlencoded_rejects_more_than_two_fields(self):
        self.assert_rejected(self.request_form([("a", "1"), ("b", "2"), ("c", "3")], "urlencoded"))

    def test_urlencoded_rejects_field_over_four_bytes(self):
        # Starlette counts encoded name + value bytes for urlencoded fields.
        self.assert_rejected(self.request_form([("a", "1234")], "urlencoded"))

    def test_urlencoded_accepts_exact_field_and_size_limits(self):
        pairs = [("a", "123"), ("b", "456")]
        self.assert_valid(self.request_form(pairs, "urlencoded"), pairs)

    def test_urlencoded_accepts_below_limits(self):
        pairs = [("a", "12")]
        self.assert_valid(self.request_form(pairs, "urlencoded"), pairs)

    def test_multipart_rejects_more_than_two_fields(self):
        self.assert_rejected(self.request_form([("a", "1"), ("b", "2"), ("c", "3")], "multipart"))

    def test_multipart_rejects_value_over_four_bytes(self):
        self.assert_rejected(self.request_form([("a", "12345")], "multipart"))

    def test_multipart_accepts_exact_field_and_size_limits(self):
        pairs = [("a", "1234"), ("b", "5678")]
        self.assert_valid(self.request_form(pairs, "multipart"), pairs)

    def test_multipart_accepts_below_limits(self):
        pairs = [("a", "123")]
        self.assert_valid(self.request_form(pairs, "multipart"), pairs)

    def test_multipart_missing_boundary_returns_client_error(self):
        response = self.client.post(
            "/form", content=b"small-body", headers={"Content-Type": "multipart/form-data"},
        )
        self.assert_rejected(response)


if __name__ == "__main__":
    unittest.main()

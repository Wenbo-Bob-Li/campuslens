"""Offline HTTP integration tests. Gemma output is mocked, never a live API call."""

from io import BytesIO
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib import error, request

from PIL import Image

from campuslens.backend import Settings
from campuslens.server import create_server


class HTTPFlowTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict("os.environ", {"GEMINI_API_KEY": "", "GEMMA_MODEL": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "data").mkdir()
        (self.root / "static").mkdir()
        catalog = Path(__file__).resolve().parent.parent / "data" / "venues.json"
        shutil.copy2(catalog, self.root / "data" / "venues.json")
        self.venue = json.loads(catalog.read_text(encoding="utf-8-sig"))[0]
        (self.root / "static" / "index.html").write_text("<!doctype html><title>CampusLens test</title>", encoding="utf-8")
        (self.root / ".env").write_text("GEMINI_API_KEY=\n", encoding="utf-8")
        self.server = create_server(Settings(self.root), port=0)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self._stop_server)
        self.base = "http://127.0.0.1:" + str(self.server.server_port)
        output = BytesIO()
        Image.new("RGB", (100, 140), "white").save(output, format="PNG")
        self.poster = output.getvalue()

    def _stop_server(self):
        self.server.shutdown()
        self.worker.join(timeout=5)
        self.server.server_close()

    def _request(self, path, *, method="GET", data=None, headers=None):
        http_request = request.Request(self.base + path, data=data, headers=headers or {}, method=method)
        try:
            response = request.urlopen(http_request, timeout=5)
        except error.HTTPError as response_error:
            response = response_error
        with response:
            return response.status, response.headers, response.read()

    def _json(self, path, *, method="GET", value=None, data=None, headers=None):
        headers = dict(headers or {})
        if value is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(value).encode("utf-8")
        status, response_headers, body = self._request(path, method=method, data=data, headers=headers)
        self.assertTrue(response_headers["Content-Type"].startswith("application/json"))
        return status, json.loads(body)

    def test_health_config_and_static_page(self):
        status, body = self._json("/api/health")
        self.assertEqual((status, body["status"]), (200, "ok"))
        status, body = self._json("/api/config")
        self.assertEqual(status, 200)
        self.assertIs(body["gemma_configured"], False)
        self.assertTrue(body["venues"])
        self.assertNotIn("api_key", body)
        status, headers, body = self._request("/")
        self.assertEqual(status, 200)
        self.assertIn(b"CampusLens test", body)
        self.assertTrue(headers["Content-Type"].startswith("text/html"))

    def test_manual_upload_confirm_save_and_reload(self):
        status, upload = self._json("/api/upload", method="POST", data=self.poster, headers={"Content-Type": "image/png"})
        self.assertEqual(status, 201)
        self.assertTrue(upload["image_url"].startswith("/uploads/"))
        activity = {
            "title": "HTTP test fictional activity",
            "location_text": self.venue["name"] + " room 101",
            "venue_id": self.venue["id"],
            "location_confirmed": True,
            "image_url": upload["image_url"],
            "is_demo": True,
        }
        status, saved = self._json("/api/events", method="POST", value=activity)
        self.assertEqual(status, 201)
        self.assertIs(saved["event"]["is_demo"], True)
        self.assertEqual(saved["event"]["lat"], self.venue["lat"])
        status, listed = self._json("/api/events")
        self.assertEqual(status, 200)
        self.assertEqual(listed["events"], [saved["event"]])
        status, headers, picture = self._request(upload["image_url"])
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/jpeg")
        with Image.open(BytesIO(picture)) as decoded:
            self.assertEqual(decoded.format, "JPEG")
        # A new service instance sees the same persisted activity.
        from campuslens.backend import CampusService
        self.assertEqual(CampusService(Settings(self.root)).store.list(), [saved["event"]])

    def test_missing_key_extract_does_not_call_model(self):
        with patch("campuslens.backend.call_gemma") as model:
            status, body = self._json("/api/extract", method="POST", data=self.poster, headers={"Content-Type": "image/png"})
        model.assert_not_called()
        self.assertEqual(status, 503)
        self.assertEqual(body["code"], "missing_api_key")

    def test_mocked_extraction_wires_image_location_and_uploaded_poster(self):
        mocked_event = {
            "title": "Mocked extraction, fictional event",
            "location_text": self.venue["name"],
            "date_text": "Friday",
            "time_text": "6 PM",
            "room": "101",
            "organizer": "Test organizers",
            "description": "Only mocked output used in this offline test.",
            "signup_url": "",
            "category": "learning",
            "evidence": [self.venue["name"]],
            "warnings": [],
        }
        with patch.dict("os.environ", {"GEMINI_API_KEY": "offline-test-key"}), patch("campuslens.backend.call_gemma", return_value=mocked_event) as model:
            status, body = self._json("/api/extract", method="POST", data=self.poster, headers={"Content-Type": "image/png"})
        self.assertEqual(status, 200)
        model.assert_called_once()
        self.assertTrue(model.call_args.args[0].startswith(b"\xff\xd8"))
        self.assertEqual(body["event"]["title"], mocked_event["title"])
        self.assertEqual(body["location_match"]["status"], "matched")
        self.assertEqual(body["location_match"]["venue_id"], self.venue["id"])
        self.assertEqual(self._request(body["image_url"])[0], 200)

    def test_cross_site_writes_are_rejected(self):
        status, body = self._json("/api/upload", method="POST", data=self.poster, headers={"Content-Type": "image/png", "Origin": "https://example.org"})
        self.assertEqual(status, 403)
        self.assertEqual(body["code"], "invalid_origin")

    def test_private_files_and_traversal_are_unavailable(self):
        for path in ("/.env", "/../.env", "/%2e%2e/.env", "/uploads/../../.env"):
            with self.subTest(path=path):
                status, body = self._json(path)
                self.assertEqual(status, 404)
                self.assertEqual(body["code"], "not_found")

    def test_invalid_upload_types_and_payloads_are_rejected(self):
        for content_type, expected_status in (("image/gif", 415), ("image/png", 400)):
            with self.subTest(content_type=content_type):
                status, _ = self._json("/api/upload", method="POST", data=b"fake image", headers={"Content-Type": content_type})
                self.assertEqual(status, expected_status)


if __name__ == "__main__":
    unittest.main()

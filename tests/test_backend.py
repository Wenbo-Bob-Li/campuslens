"""Offline checks for location, model output, uploaded files and persistence."""

from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from campuslens.backend import (
    AppError, EventStore, Settings, call_gemma, match_location,
    parse_extraction, safe_signup_url, validate_event, validate_image,
)
from campuslens.server import safe_static_path


VENUES = [
    {"id": "price-center", "name": "Price Center", "aliases": ["PC"], "lat": 32.8797, "lng": -117.2362},
    {"id": "dib", "name": "Design and Innovation Building", "aliases": ["DIB", "Design & Innovation Building"], "lat": 32.8781, "lng": -117.2335},
]


def image_bytes(image_format="PNG", size=(80, 100)):
    output = BytesIO()
    Image.new("RGB", size, "white").save(output, image_format)
    return output.getvalue()


class LocationTests(unittest.TestCase):
    def test_room_suffix_matches_building(self):
        result = match_location("Price Center West Ballroom", VENUES)
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["venue_id"], "price-center")

    def test_multiple_named_buildings_require_confirmation(self):
        result = match_location("Price Center or DIB", VENUES)
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["venue_id"])
        self.assertEqual(len(result["candidates"]), 2)

    def test_short_alias_must_be_a_whole_word(self):
        self.assertEqual(match_location("audible PCboard", VENUES)["status"], "unmatched")
        self.assertEqual(match_location("DIB 208", VENUES)["venue_id"], "dib")

    def test_neighboring_building_names_require_full_words(self):
        venues = [
            {"id": "center-hall", "name": "Center Hall", "aliases": []},
            {"id": "muir-college", "name": "Muir College", "aliases": []},
            {"id": "muir-biology", "name": "Muir Biology Building", "aliases": ["Muir Biology"]},
        ]
        self.assertEqual(match_location("Center Hallway 101", venues)["status"], "unmatched")
        self.assertEqual(match_location("Muir Biology 120", venues)["venue_id"], "muir-biology")
        self.assertEqual(match_location("Muir College", venues)["venue_id"], "muir-college")

    def test_contained_short_name_yields_to_specific_building_name(self):
        venues = [
            {"id": "muir-college", "name": "Muir College", "aliases": []},
            {"id": "muir-biology", "name": "Muir College Biology Building", "aliases": []},
        ]
        self.assertEqual(match_location("Muir College Biology Building, Room 120", venues)["venue_id"], "muir-biology")
        separate = match_location("Muir College Biology Building or Muir College", venues)
        self.assertEqual(separate["status"], "ambiguous")
        self.assertEqual(len(separate["candidates"]), 2)

    def test_shared_alias_stays_ambiguous_and_generic_alias_is_ignored(self):
        venues = [
            {"id": "first", "name": "First Named Building", "aliases": ["Shared Pavilion", "Hall", "UCSD"]},
            {"id": "second", "name": "Second Named Building", "aliases": ["Shared Pavilion", "Center", "Main"]},
        ]
        shared = match_location("Shared Pavilion, room 100", venues)
        self.assertEqual(shared["status"], "ambiguous")
        self.assertIsNone(shared["venue_id"])
        self.assertEqual(match_location("UCSD Main Center Hall", venues)["status"], "unmatched")

    def test_student_services_center_does_not_become_student_center(self):
        venues = [
            {"id": "student-center", "name": "Student Center", "aliases": []},
            {"id": "student-services", "name": "Student Services Center", "aliases": ["SSC"]},
        ]
        self.assertEqual(match_location("Student Services Center, room 2", venues)["venue_id"], "student-services")


class ImageTests(unittest.TestCase):
    def test_accepts_real_png(self):
        normalized = validate_image(image_bytes(), "image/png")
        with Image.open(BytesIO(normalized)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (80, 100))

    def test_rejects_content_type_disagreement_and_fake_image(self):
        for payload, content_type in ((image_bytes(), "image/jpeg"), (b"not an image", "image/png")):
            with self.subTest(content_type=content_type), self.assertRaises(AppError):
                validate_image(payload, content_type)

    def test_large_side_is_downscaled(self):
        normalized = validate_image(image_bytes(size=(3000, 1200)), "image/png")
        with Image.open(BytesIO(normalized)) as image:
            self.assertEqual(image.size, (2400, 960))

    def test_rejects_tiny_image(self):
        with self.assertRaises(AppError):
            validate_image(image_bytes(size=(1, 1)), "image/png")


class ExtractionTests(unittest.TestCase):
    def test_categories_match_frontend_and_normalize_legacy_values(self):
        expected = {
            "academic": "learning", "workshop": "learning", "volunteering": "other",
            "unknown-category": "other", "": "other", "Learning": "learning",
            "social": "social", "arts": "arts", "career": "career", "sports": "sports",
        }
        for category, normalized in expected.items():
            with self.subTest(category=category):
                result = parse_extraction(json.dumps({"title": "Demo", "category": category}))
                self.assertEqual(result["category"], normalized)

    def test_fenced_model_json_is_normalized(self):
        result = parse_extraction('```json\n{"title":" Demo ","evidence":["Demo"],"signup_url":"javascript:alert(1)"}\n```')
        self.assertEqual(result["title"], "Demo")
        self.assertEqual(result["signup_url"], "")
        self.assertEqual(result["date_text"], "")

    def test_rejects_invalid_and_wrongly_typed_model_output(self):
        for output in ('not JSON', '{"nothing":1}', '{"title":{"nested":true}}', '{"title":""}'):
            with self.subTest(output=output), self.assertRaises(AppError) as caught:
                parse_extraction(output)
            self.assertEqual(caught.exception.code, "invalid_model_response")

    def test_missing_key_never_makes_network_request(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), patch("campuslens.backend.dotenv_values", return_value={}), patch("campuslens.backend.request.urlopen") as network, self.assertRaises(AppError) as caught:
            call_gemma(b"image", Settings(Path(".")))
        network.assert_not_called()
        self.assertEqual(caught.exception.code, "missing_api_key")

    def test_local_key_is_reloaded_without_restart(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"GEMINI_API_KEY": "", "GEMMA_MODEL": ""}):
            root = Path(directory)
            settings = Settings(root)
            (root / ".env").write_text("GEMINI_API_KEY=\n", encoding="utf-8")
            self.assertEqual(settings.credentials()[0], "")
            (root / ".env").write_text("GEMINI_API_KEY=test-key\n", encoding="utf-8")
            self.assertEqual(settings.credentials()[0], "test-key")

    def test_model_response_parts_are_parsed(self):
        body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"title":"Workshop","location_text":"DIB"}'}]}}]}
        with patch("campuslens.backend.request.urlopen") as network:
            network.return_value.__enter__.return_value.read.return_value = json.dumps(body).encode()
            result = call_gemma(b"image", Settings(Path("."), "test-key"))
        self.assertEqual(result["title"], "Workshop")
        sent = network.call_args.args[0]
        self.assertNotIn("test-key", sent.full_url)
        sent_payload = json.loads(sent.data)
        self.assertEqual(sent_payload["generationConfig"]["thinkingConfig"]["thinkingLevel"], "minimal")


class EventTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = {"title": "Workshop", "location_text": "DIB 208", "venue_id": "dib", "location_confirmed": True}

    def tearDown(self):
        self.temporary.cleanup()

    def test_selected_building_uses_catalog_coordinates(self):
        event = validate_event({**self.value, "lat": 0, "lng": 0}, VENUES, self.root)
        self.assertEqual(event["lat"], VENUES[1]["lat"])
        self.assertEqual(event["location_precision"], "building")

    def test_demo_flag_defaults_false_and_preserves_explicit_boolean(self):
        self.assertIs(validate_event(self.value, VENUES, self.root)["is_demo"], False)
        for flag in (False, True):
            with self.subTest(flag=flag):
                event = validate_event({**self.value, "is_demo": flag}, VENUES, self.root)
                saved = EventStore(self.root / "demo-flags.db").add(event)
                self.assertIs(saved["is_demo"], flag)

    def test_demo_flag_rejects_strings_and_other_non_booleans(self):
        for flag in ("true", "false", 0, 1, None):
            with self.subTest(flag=flag), self.assertRaises(AppError) as caught:
                validate_event({**self.value, "is_demo": flag}, VENUES, self.root)
            self.assertEqual(caught.exception.code, "invalid_demo_flag")

    def test_manual_marker_requires_finite_campus_coordinates(self):
        for lat, lng in ((0, 0), (float("nan"), -117.23), (True, -117.23), (32.87, "-117.23")):
            with self.subTest(lat=lat), self.assertRaises(AppError):
                validate_event({**self.value, "venue_id": None, "lat": lat, "lng": lng}, VENUES, self.root)
        event = validate_event({**self.value, "venue_id": None, "lat": 32.88, "lng": -117.23}, VENUES, self.root)
        self.assertEqual(event["location_precision"], "manual")

    def test_unconfirmed_or_unknown_building_is_rejected(self):
        for changes in ({"location_confirmed": False}, {"venue_id": "missing"}, {"title": ""}, {"location_text": ""}):
            with self.subTest(changes=changes), self.assertRaises(AppError):
                validate_event({**self.value, **changes}, VENUES, self.root)

    def test_image_must_be_a_real_local_uploaded_file(self):
        for image_url in ("https://example.com/poster.jpg", "/uploads/../../.env", "/uploads/" + "a" * 32 + ".jpg"):
            with self.subTest(image_url=image_url), self.assertRaises(AppError):
                validate_event({**self.value, "image_url": image_url}, VENUES, self.root)
        filename = "b" * 32 + ".jpg"
        (self.root / filename).write_bytes(image_bytes("JPEG"))
        event = validate_event({**self.value, "image_url": "/uploads/" + filename}, VENUES, self.root)
        self.assertEqual(event["image_url"], "/uploads/" + filename)

    def test_sqlite_persists_unicode_and_ids(self):
        path = self.root / "events.db"
        event = validate_event({**self.value, "title": "校园工作坊"}, VENUES, self.root)
        saved = EventStore(path).add(event)
        self.assertEqual(EventStore(path).list(), [saved])
        self.assertEqual(len(saved["id"]), 32)

    def test_safe_url_accepts_only_real_http_urls(self):
        self.assertEqual(safe_signup_url("https://example.com/signup"), "https://example.com/signup")
        for value in ("javascript:alert(1)", "//evil.test", "https://user:pass@example.com", "https://example.com:bad"):
            self.assertEqual(safe_signup_url(value), "")


class PathTests(unittest.TestCase):
    def test_static_root_does_not_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "static"
            static.mkdir()
            (static / "index.html").write_text("hello", encoding="utf-8")
            (root / ".env").write_text("secret", encoding="utf-8")
            self.assertEqual(safe_static_path(static, "/"), static / "index.html")
            for path in ("/../.env", "/%2e%2e/.env", "/..%5c.env", "/%00", "/.env"):
                with self.subTest(path=path):
                    self.assertIsNone(safe_static_path(static, path))


if __name__ == "__main__":
    unittest.main()

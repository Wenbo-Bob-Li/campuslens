"""Integrity and useful location matching checks for the bundled UCSD catalog."""

from pathlib import Path
import unittest
from urllib.parse import urlsplit

from campuslens.backend import (
    GENERIC_LOCATION_NAMES, UCSD_BOUNDS, match_location, normalize_location, read_venues,
)


CATALOG = Path(__file__).resolve().parent.parent / "data" / "venues.json"
LEGACY_IDS = {
    "price-center", "geisel-library", "design-and-innovation-building", "rimac",
    "epstein-family-amphitheater", "student-center", "conrad-prebys-music-center",
    "atkinson-hall",
}


class VenueCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.venues = read_venues(CATALOG)
        cls.by_id = {venue["id"]: venue for venue in cls.venues}

    def test_catalog_expands_coverage_and_keeps_existing_event_ids(self):
        self.assertGreaterEqual(len(self.venues), 100)
        self.assertTrue(LEGACY_IDS.issubset(self.by_id))
        self.assertEqual(len(self.by_id), len(self.venues))

    def test_every_location_has_campus_coordinates_source_and_specific_aliases(self):
        min_lat, max_lat, min_lng, max_lng = UCSD_BOUNDS
        for venue in self.venues:
            with self.subTest(venue=venue["id"]):
                self.assertTrue(venue["name"].strip())
                self.assertTrue(min_lat <= venue["lat"] <= max_lat)
                self.assertTrue(min_lng <= venue["lng"] <= max_lng)
                self.assertEqual(venue["precision"], "building")
                source = urlsplit(venue["source_url"])
                self.assertEqual(source.scheme, "https")
                self.assertTrue(source.hostname)
                self.assertIsInstance(venue["aliases"], list)
                for alias in venue["aliases"]:
                    normalized = normalize_location(alias)
                    self.assertGreater(len(normalized), 1)
                    self.assertNotIn(normalized, GENERIC_LOCATION_NAMES)
                    self.assertTrue(any(character.isalpha() for character in normalized))

    def test_new_buildings_and_poster_abbreviations(self):
        expected = {
            "Center Hall, room 101": "ucsd-1760",
            "CENTR 101": "ucsd-1760",
            "M2B 120": "ucsd-1737",
            "Muir Biology Building, room 120": "ucsd-1737",
            "Warren Lecture Hall 2005": "ucsd-2037",
            "WLH-2005": "ucsd-2037",
            "CSE 1202": "ucsd-2122",
            "EBU-3B, room 1202": "ucsd-2122",
        }
        for text, venue_id in expected.items():
            with self.subTest(text=text):
                result = match_location(text, self.venues)
                self.assertEqual(result["status"], "matched")
                self.assertEqual(result["venue_id"], venue_id)

    def test_original_poster_locations_remain_compatible(self):
        expected = {
            "Price Center — West Ballroom": "price-center",
            "Design and Innovation Building (DIB), Room 208": "design-and-innovation-building",
            "The Basement": "design-and-innovation-building",
        }
        for text, venue_id in expected.items():
            with self.subTest(text=text):
                self.assertEqual(match_location(text, self.venues)["venue_id"], venue_id)
        self.assertEqual(match_location("Location to be announced", self.venues)["status"], "unmatched")

    def test_distinct_buildings_and_shared_names_stay_ambiguous(self):
        result = match_location("Center Hall or Warren Lecture Hall", self.venues)
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["venue_id"])
        ids = {venue["id"] for venue in result["candidates"]}
        self.assertTrue({"ucsd-1760", "ucsd-2037"}.issubset(ids))
        shared = match_location("GSA, Student Center A", self.venues)
        self.assertEqual(shared["status"], "ambiguous")
        self.assertIsNone(shared["venue_id"])
        self.assertEqual({venue["id"] for venue in shared["candidates"]}, {"ucsd-1988", "ucsd-1990"})


if __name__ == "__main__":
    unittest.main()

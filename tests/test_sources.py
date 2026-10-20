import unittest
from unittest.mock import patch

from job_founder.sources import fetch_source, parse_source_spec, search_configured_sources


class SourceConnectorTests(unittest.TestCase):
    def test_source_identifiers_are_validated(self):
        self.assertEqual(parse_source_spec("greenhouse:acme-board"), ("greenhouse", "acme-board"))
        self.assertEqual(parse_source_spec("lever:acme"), ("lever", "acme"))
        for value in ("https://evil.example", "greenhouse:../private", "unknown:acme", "lever:"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_source_spec(value)

    @patch("job_founder.sources._safe_json")
    def test_greenhouse_jobs_are_normalized_and_skills_scored(self, safe_json):
        safe_json.return_value = {"jobs": [{
            "id": 1,
            "title": "Python Engineer",
            "location": {"name": "Remote - France"},
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
            "content": "<p>Python and PostgreSQL services</p>",
            "updated_at": "2026-10-19T10:00:00Z",
        }]}
        jobs = fetch_source("greenhouse:acme", {"skills": "Python, SQL"})
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["remote"], "Télétravail")
        self.assertEqual(jobs[0]["skills"], ["Python"])
        self.assertEqual(jobs[0]["score"], 65)
        self.assertFalse(jobs[0]["is_demo"])
        self.assertEqual(jobs[0]["link"], "https://boards.greenhouse.io/acme/jobs/1")

    @patch("job_founder.sources._safe_json")
    def test_lever_jobs_and_per_source_errors_are_reported(self, safe_json):
        safe_json.return_value = [{
            "text": "Analyst",
            "categories": {"location": "Lyon, France", "commitment": "Full-time"},
            "hostedUrl": "https://jobs.lever.co/acme/1",
            "descriptionPlain": "Reporting and SQL",
            "workplaceType": "hybrid",
            "createdAt": 1792400000000,
        }]
        jobs, errors = search_configured_sources(["lever:acme"], {"skills": "SQL"})
        self.assertEqual(errors, [])
        self.assertEqual(jobs[0]["remote"], "Hybride")
        self.assertEqual(jobs[0]["skills"], ["SQL"])
        self.assertEqual(jobs[0]["source"], "Lever · acme")

    @patch("job_founder.sources._safe_json", side_effect=RuntimeError("hors ligne"))
    def test_source_failure_is_not_mistaken_for_an_empty_success(self, _safe_json):
        jobs, errors = search_configured_sources(["greenhouse:acme"], {})
        self.assertEqual(jobs, [])
        self.assertIn("hors ligne", errors[0])


if __name__ == "__main__":
    unittest.main()

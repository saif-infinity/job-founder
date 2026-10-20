import unittest

from job_founder.navigation import _is_public_http_url, diagnose_page


class NavigationDiagnosisTests(unittest.TestCase):
    def test_classifies_ats_and_finds_application_link_and_required_fields(self):
        report = diagnose_page(
            "https://jobs.greenhouse.io/acme/backend",
            "Backend Engineer",
            "Apply for this job",
            [{"text": "Apply now", "href": "/applications/new"}],
            [{"name": "email", "label": "Email address", "type": "email", "required": True}],
            form_found=False,
        )
        self.assertEqual(report.platform, "ats")
        self.assertEqual(report.application_url, "https://jobs.greenhouse.io/applications/new")
        self.assertEqual(report.required_fields, ["Email address"])
        self.assertNotIn("captcha_detecte", report.blockers)

    def test_detects_human_blockers_without_bypassing_them(self):
        report = diagnose_page(
            "https://careers.example.org/job",
            "Sign in to apply",
            "Verify you are human. This job has expired.",
            [],
            [{"name": "password", "type": "password", "required": True}],
        )
        self.assertTrue(report.expired)
        self.assertIn("captcha_detecte", report.blockers)
        self.assertIn("login_requis", report.blockers)
        self.assertIn("offre_expiree", report.blockers)

    def test_rejects_non_web_and_local_urls(self):
        for url in ("file:///etc/passwd", "javascript:alert(1)", "http://localhost", "http://127.0.0.1"):
            self.assertFalse(_is_public_http_url(url), url)
        self.assertTrue(_is_public_http_url("https://example.org/job"))


if __name__ == "__main__":
    unittest.main()

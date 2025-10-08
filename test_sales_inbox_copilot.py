import unittest
import os
import sys
import tempfile
import shutil

# Mock the agents module to avoid requiring openai-agents for tests
class MockModule:
    pass

mock_agents = MockModule()

class MockAgent:
    def __init__(self, *args, **kwargs):
        pass

mock_agents.Agent = MockAgent
mock_agents.Handoff = type('Handoff', (), {})
mock_agents.Session = type('Session', (), {})

mock_tool = MockModule()
def mock_function_tool(**kwargs):
    def decorator(func):
        return func
    return decorator
mock_tool.function_tool = mock_function_tool

sys.modules['agents'] = mock_agents
sys.modules['agents.tool'] = mock_tool

from sales_inbox_copilot import simple_search, search_kb, qualify_lead, draft_email


class TestSimpleSearch(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []

        # Create test markdown files
        test_content = {
            "test1.md": "This is a test file about pricing and costs.",
            "test2.md": "Security features include SSO and encryption.",
            "test3.md": "API documentation and integration guides."
        }

        for filename, content in test_content.items():
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            self.test_files.append(filepath)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_simple_search_returns_results(self):
        results = simple_search(self.test_files, "pricing", top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["path"], self.test_files[0])

    def test_simple_search_ranking(self):
        results = simple_search(self.test_files, "security SSO", top_k=3)
        self.assertGreater(len(results), 0)
        # File with more matches should rank higher
        self.assertIn("security", results[0]["snippet"].lower())

    def test_simple_search_top_k_limit(self):
        results = simple_search(self.test_files, "test", top_k=2)
        self.assertLessEqual(len(results), 2)

    def test_simple_search_no_matches(self):
        results = simple_search(self.test_files, "nonexistent", top_k=3)
        self.assertEqual(len(results), 0)

    def test_simple_search_handles_missing_file(self):
        # Add a non-existent file to the list
        files_with_missing = self.test_files + ["/nonexistent/file.md"]
        # Should not crash, should handle gracefully
        results = simple_search(files_with_missing, "test", top_k=3)
        self.assertIsInstance(results, list)


class TestSearchKB(unittest.TestCase):
    def test_search_kb_empty_query(self):
        result = search_kb("")
        self.assertIn("error", result)
        self.assertEqual(result["results"], [])

    def test_search_kb_whitespace_query(self):
        result = search_kb("   ")
        self.assertIn("error", result)
        self.assertEqual(result["results"], [])

    def test_search_kb_returns_dict(self):
        result = search_kb("test query")
        self.assertIsInstance(result, dict)
        self.assertIn("results", result)


class TestQualifyLead(unittest.TestCase):
    def test_qualify_enterprise_lead(self):
        message = "We need SSO with Okta for our team of over 100 seats"
        result = qualify_lead(message)
        self.assertEqual(result["segment"], "enterprise")
        self.assertIn("security/enterprise", result["tags"])
        self.assertIn("large-team", result["tags"])

    def test_qualify_enterprise_security(self):
        message = "Do you have SOC 2 and ISO 27001 compliance?"
        result = qualify_lead(message)
        self.assertEqual(result["segment"], "enterprise")
        self.assertIn("security/enterprise", result["tags"])

    def test_qualify_buying_signal(self):
        message = "We'd like to start a POC next week"
        result = qualify_lead(message)
        self.assertIn("buying-signal", result["tags"])

    def test_qualify_general_lead(self):
        message = "Tell me more about your product"
        result = qualify_lead(message)
        self.assertIn("general", result["tags"])
        self.assertEqual(result["segment"], "pro")

    def test_qualify_pro_segment(self):
        message = "Looking for a trial for my small team"
        result = qualify_lead(message)
        self.assertEqual(result["segment"], "pro")


class TestDraftEmail(unittest.TestCase):
    def test_draft_email_structure(self):
        lead = {"segment": "enterprise", "tags": ["security/enterprise"]}
        kb_snippets = [
            {"path": "./kb/security.md", "snippet": "We support SSO"}
        ]
        result = draft_email("John", "test message", lead, kb_snippets)

        self.assertIn("email_body", result)
        self.assertIn("John", result["email_body"])
        self.assertIn("Enterprise", result["email_body"])

    def test_draft_email_includes_snippets(self):
        lead = {"segment": "pro", "tags": ["general"]}
        kb_snippets = [
            {"path": "./kb/pricing.md", "snippet": "Pro plan is $99"},
            {"path": "./kb/features.md", "snippet": "Export to CSV"}
        ]
        result = draft_email("Jane", "pricing question", lead, kb_snippets)

        self.assertIn("pricing.md", result["email_body"])
        self.assertIn("features.md", result["email_body"])

    def test_draft_email_empty_snippets(self):
        lead = {"segment": "pro", "tags": ["general"]}
        result = draft_email("Test", "message", lead, [])

        self.assertIn("email_body", result)
        self.assertIsInstance(result["email_body"], str)

    def test_draft_email_pro_segment(self):
        lead = {"segment": "pro", "tags": ["buying-signal"]}
        kb_snippets = []
        result = draft_email("Alice", "test", lead, kb_snippets)

        self.assertIn("Pro", result["email_body"])


if __name__ == "__main__":
    unittest.main()

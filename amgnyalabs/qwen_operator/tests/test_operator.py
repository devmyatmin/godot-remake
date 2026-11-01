import unittest

from operator import AdapterError, extract_json_object, validate_request
from gateway import PROTOCOL


class AdapterTests(unittest.TestCase):
    def test_extracts_json_after_cli_banner(self):
        raw = 'llama.cpp startup log\n{"tool":"inspect_project"}\n'
        self.assertEqual(extract_json_object(raw), {"tool": "inspect_project"})

    def test_rejects_non_json_output(self):
        with self.assertRaises(AdapterError):
            extract_json_object("I will inspect the project now.")

    def test_rejects_unknown_tool(self):
        request = {
            "protocol": PROTOCOL,
            "request_id": "abc",
            "tool": "shell",
            "arguments": {"command": "rm -rf /"},
            "permission": "read",
        }
        with self.assertRaises(AdapterError):
            validate_request(request, "abc")

    def test_rejects_write_permission(self):
        request = {
            "protocol": PROTOCOL,
            "request_id": "abc",
            "tool": "inspect_project",
            "arguments": {"path": "."},
            "permission": "write_workspace",
        }
        with self.assertRaises(AdapterError):
            validate_request(request, "abc")

    def test_rejects_wrong_request_id(self):
        request = {
            "protocol": PROTOCOL,
            "request_id": "not-abc",
            "tool": "inspect_project",
            "arguments": {"path": "."},
            "permission": "read",
        }
        with self.assertRaises(AdapterError):
            validate_request(request, "abc")


if __name__ == "__main__":
    unittest.main()

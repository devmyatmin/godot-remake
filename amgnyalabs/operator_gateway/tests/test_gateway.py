import tempfile
import unittest
from pathlib import Path

from gateway import PROTOCOL, ReadOnlyGateway


def request(tool, arguments, *, permission="read", request_id="test-1"):
    return {
        "protocol": PROTOCOL,
        "request_id": request_id,
        "tool": tool,
        "arguments": arguments,
        "permission": permission,
    }


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "Assets").mkdir()
        (self.root / "Assets" / "tree.png").write_bytes(b"png")
        (self.root / "Assets" / "rock.mesh").write_bytes(b"mesh")
        (self.root / "readme.txt").write_text("sample", encoding="utf-8")
        unity = self.root / "UnitySample"
        (unity / "Assets").mkdir(parents=True)
        (unity / "Packages").mkdir()
        (unity / "ProjectSettings").mkdir()
        (unity / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 2022.3.10f1\n", encoding="utf-8"
        )
        (unity / "Packages" / "manifest.json").write_text(
            '{"dependencies":{"com.unity.test-framework":"1.1.33"}}', encoding="utf-8"
        )
        (unity / "Assets" / "Sample.prefab").write_text(
            "%YAML 1.1\n--- !u!1 &100\nGameObject:\n  m_External: {fileID: 2100000, guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, type: 2}\n",
            encoding="utf-8",
        )
        (unity / "Assets" / "Texture.png").write_bytes(b"png")
        (unity / "Assets" / "Texture.png.meta").write_text(
            "fileFormatVersion: 2\nguid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
            encoding="utf-8",
        )
        (unity / "Assets" / "Sample.prefab.meta").write_text(
            "fileFormatVersion: 2\nguid: 0123456789abcdef0123456789abcdef\n",
            encoding="utf-8",
        )
        self.gateway = ReadOnlyGateway(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_inspect_unity_project_reads_bounded_project_metadata(self):
        response = self.gateway.handle(request(
            "inspect_unity_project", {"path": "UnitySample", "max_files": 100}
        ))
        self.assertEqual(response["status"], "ok")
        result = response["result"]
        self.assertTrue(result["is_unity_project"])
        self.assertEqual(result["unity_editor_version"], "2022.3.10f1")
        self.assertEqual(result["package_dependency_count"], 1)
        self.assertEqual(result["unique_meta_guid_count"], 2)
        self.assertEqual(result["yaml_object_class_id_counts"]["1"], 1)
        self.assertEqual(
            result["guid_to_asset"]["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
            "Assets/Texture.png",
        )
        self.assertEqual(result["yaml_references"][0]["resolution"], "resolved")
        self.assertEqual(
            result["yaml_references"][0]["resolved_asset"], "Assets/Texture.png"
        )
        self.assertEqual(
            result["support_matrix"]["text_yaml_object_ids_and_pptr_references"],
            "partial",
        )
        self.assertEqual(result["support_level"], "partial_metadata_and_reference_inspection")

    def test_inspect_asset_returns_metadata_only(self):
        response = self.gateway.handle(request("inspect_asset", {"path": "Assets/tree.png"}))
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["result"]["extension"], ".png")
        self.assertEqual(response["result"]["size_bytes"], 3)
        self.assertNotIn("content", response["result"])

    def test_search_filters_by_name_and_extension(self):
        response = self.gateway.handle(request(
            "search_assets",
            {"query": "tree", "extensions": [".png"], "path": "Assets"},
        ))
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["result"]["match_count"], 1)
        self.assertEqual(response["result"]["matches"][0]["path"], "Assets/tree.png")

    def test_project_inventory_is_bounded(self):
        response = self.gateway.handle(request("inspect_project", {"path": ".", "max_entries": 1}))
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["result"]["entry_count"], 1)
        self.assertTrue(response["result"]["truncated"])

    def test_parent_traversal_is_rejected(self):
        response = self.gateway.handle(request("inspect_asset", {"path": "../outside.txt"}))
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["errors"][0]["code"], "path_outside_workspace")

    def test_absolute_path_is_rejected(self):
        response = self.gateway.handle(request("inspect_asset", {"path": str(self.root / "readme.txt")}))
        self.assertEqual(response["status"], "error")

    def test_write_permission_is_denied(self):
        response = self.gateway.handle(request("inspect_project", {}, permission="write_workspace"))
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["errors"][0]["code"], "permission_denied")

    def test_unknown_tool_is_denied(self):
        response = self.gateway.handle(request("shell", {"command": "echo unsafe"}))
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["errors"][0]["code"], "unknown_tool")

    def test_symlink_is_not_followed(self):
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "outside-link.txt"
        try:
            link.symlink_to(outside)
            response = self.gateway.handle(request("inspect_asset", {"path": "outside-link.txt"}))
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["errors"][0]["code"], "symlink_denied")
        finally:
            if link.is_symlink():
                link.unlink()
            if outside.exists():
                outside.unlink()


if __name__ == "__main__":
    unittest.main()

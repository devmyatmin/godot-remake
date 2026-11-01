import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unity_binary_importer import import_unity_file


class FakeImage:
    def save(self, path, format=None):
        if hasattr(path, "write"):
            path.write(b"PNGDATA")
        else:
            Path(path).write_bytes(b"PNGDATA")


class FakeParsed:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeObject:
    def __init__(self, path_id, type_name, name, parsed=None, error=None):
        self.path_id = path_id
        self.type = types.SimpleNamespace(name=type_name)
        self._name = name
        self._parsed = parsed
        self._error = error

    def peek_name(self):
        return self._name

    def parse_as_object(self):
        if self._error:
            raise self._error
        return self._parsed


class UnityBinaryImporterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source_dir = self.root / "original"
        self.source_dir.mkdir()
        self.source = self.source_dir / "sharedassets0.assets"
        self.source.write_bytes(b"original-unity-data")
        self.output = self.root / "generated"

    def tearDown(self):
        self.temp.cleanup()

    def test_exports_supported_objects_and_keeps_partial_results(self):
        objects = [
            FakeObject(1, "Texture2D", "Ocean", FakeParsed(m_Name="Ocean", image=FakeImage())),
            FakeObject(2, "Mesh", "Island", FakeParsed(m_Name="Island", export=lambda: "o Island\nv 0 0 0\n")),
            FakeObject(3, "AudioClip", "Wave", FakeParsed(samples={"Wave": b"RIFFDATA"})),
            FakeObject(4, "Material", "Water", FakeParsed(m_Name="Water")),
            FakeObject(5, "Texture2D", "Broken", error=ValueError("bad texture")),
        ]
        fake_unitypy = types.SimpleNamespace(load=lambda path: types.SimpleNamespace(objects=objects))
        with patch.dict(sys.modules, {"UnityPy": fake_unitypy}):
            report = import_unity_file(self.source, self.output)

        self.assertEqual(report["exported_objects"], 3)
        self.assertEqual(report["metadata_only_objects"], 1)
        self.assertEqual(report["failed_objects"], 1)
        self.assertTrue((self.output / "sharedassets0.assets" / "1_Ocean.png").is_file())
        self.assertTrue((self.output / "sharedassets0.assets" / "2_Island.obj").is_file())
        self.assertTrue((self.output / "sharedassets0.assets" / "3_Wave_Wave.wav").is_file())
        self.assertEqual(self.source.read_bytes(), b"original-unity-data")
        saved_report = json.loads(
            (self.output / "sharedassets0.assets" / "import_report.json").read_text()
        )
        self.assertEqual(saved_report["failed_objects"], 1)

    def test_rejects_output_inside_original_source_directory(self):
        fake_unitypy = types.SimpleNamespace(load=lambda path: types.SimpleNamespace(objects=[]))
        with patch.dict(sys.modules, {"UnityPy": fake_unitypy}):
            with self.assertRaisesRegex(ValueError, "outside the original source directory"):
                import_unity_file(self.source, self.source_dir / "generated")


    def test_existing_generated_file_is_not_overwritten(self):
        destination = self.output / "sharedassets0.assets"
        destination.mkdir(parents=True)
        existing = destination / "1_Ocean.png"
        existing.write_bytes(b"keep-this")
        objects = [
            FakeObject(1, "Texture2D", "Ocean", FakeParsed(m_Name="Ocean", image=FakeImage())),
        ]
        fake_unitypy = types.SimpleNamespace(load=lambda path: types.SimpleNamespace(objects=objects))
        with patch.dict(sys.modules, {"UnityPy": fake_unitypy}):
            report = import_unity_file(self.source, self.output)
        self.assertEqual(report["failed_objects"], 1)
        self.assertEqual(existing.read_bytes(), b"keep-this")

    def test_rejects_invalid_object_limit(self):
        with self.assertRaisesRegex(ValueError, "max_objects"):
            import_unity_file(self.source, self.output, 0)


if __name__ == "__main__":
    unittest.main()

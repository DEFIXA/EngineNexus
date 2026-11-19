import tempfile
import unittest
import zipfile
from pathlib import Path
from install_upgrade import merge, safe_name

class TestInstaller(unittest.TestCase):
    def test_reject_traversal(self):
        with self.assertRaises(ValueError):
            safe_name("../malicious.py")

    def test_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            original = Path(d) / "original.zip"
            upgraded = Path(d) / "upgraded.zip"
            with zipfile.ZipFile(original, "w") as z:
                z.writestr("original_tool.py", "original contents")
            merge(original, upgraded)
            with zipfile.ZipFile(upgraded) as z:
                self.assertEqual(z.read("original_tool.py"), b"original contents")
                self.assertIn("blender_advancements_v2/SKILL.md", z.namelist())

if __name__ == "__main__":
    unittest.main()

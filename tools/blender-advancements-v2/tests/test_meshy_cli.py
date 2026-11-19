import unittest
from asset_factory.spec import AssetSpec
from asset_factory.meshy_cli import _create_command, _task_id

class TestMeshyCli(unittest.TestCase):
    def test_text_prompt(self):
        spec = AssetSpec("test_prop", "ancient magic amulet", "prop", backend="meshy")
        resource, cmd = _create_command(spec, "meshy")
        self.assertEqual(resource, "text-to-3d")
        self.assertIn("ancient magic amulet", cmd)
        self.assertIn("smart-topology", cmd)

    def test_multiview(self):
        spec = AssetSpec("test_dragon", "dragon", "creature",
                         references=["front.png", "side.png"], backend="meshy")
        resource, cmd = _create_command(spec, "meshy")
        self.assertEqual(resource, "multi-image-to-3d")
        self.assertIn("--data", cmd)

    def test_resume_requires_real_id(self):
        with self.assertRaises(RuntimeError):
            _task_id({"result": {}})
        self.assertEqual(_task_id({"result": {"submission": {"task_id": "abc"}}}), "abc")

if __name__ == "__main__":
    unittest.main()

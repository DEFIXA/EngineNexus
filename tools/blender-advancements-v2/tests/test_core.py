import json
import tempfile
import unittest
from pathlib import Path
from asset_factory.spec import AssetSpec
from asset_factory.router import route
from asset_factory.quality import decide


class TestAssetFactory(unittest.TestCase):
    def test_creature_requires_retopology(self):
        spec = AssetSpec("dragon_leg_01", "dragon leg", "creature", animated=True)
        r = route(spec)
        self.assertEqual(r.backend, "blender")
        self.assertTrue(r.requires_human_retopology)
        self.assertIn("rig_and_pose_tests", r.stages)

    def test_cloud_requires_consent(self):
        spec = AssetSpec("prop_01", "stone relic", "prop", backend="meshy")
        self.assertTrue(route(spec).requires_paid_consent)

    def test_bad_identifier_rejected(self):
        with self.assertRaises(ValueError):
            AssetSpec("../escape", "tree", "tree").validate()

    def test_spec_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "spec.json"
            spec = AssetSpec("tree_01", "twisted tree", "tree")
            spec.save(p)
            self.assertEqual(AssetSpec.load(p).to_dict(), spec.to_dict())

    def test_qc_does_not_claim_engine_validity(self):
        qc = {
            "objects": [{"name": "SM_tree", "triangles": 200, "non_manifold_edges": 0,
                         "loose_vertices": 0, "has_uv": True, "negative_scale": False}],
            "runtime_triangles": 200,
        }
        d = decide(qc, animated=False, references=True, triangle_budget=1000)
        self.assertTrue(d.technical_pass)
        self.assertTrue(d.visual_review_required)
        self.assertTrue(d.engine_validation_required)

    def test_qc_rejects_bad_mesh(self):
        qc = {"objects": [{"name": "bad", "triangles": 20, "non_manifold_edges": 5,
                            "loose_vertices": 0, "has_uv": False}],
              "runtime_triangles": 20}
        self.assertFalse(decide(qc, animated=True, references=False, triangle_budget=100).technical_pass)


if __name__ == "__main__":
    unittest.main()

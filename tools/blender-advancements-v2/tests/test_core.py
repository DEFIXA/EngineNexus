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

    def test_arbitrary_prop_routes_to_supported_generator(self):
        spec = AssetSpec("sword_01", "ancient sword", "weapon")
        r = route(spec)
        self.assertEqual(r.backend, "meshy")
        self.assertTrue(r.requires_paid_consent)

    def test_unreferenced_creature_head_needs_3d_ai(self):
        spec = AssetSpec("head_01", "dragon head", "creature")
        self.assertEqual(route(spec).backend, "meshy")

    def test_reference_creature_prefers_image_to_3d(self):
        spec = AssetSpec("dragon_ref", "dragon leg", "creature",
                         references=["dragon_front.png"])
        r = route(spec)
        self.assertEqual(r.backend, "meshy")
        self.assertTrue(r.requires_paid_consent)
        self.assertIn("blender", r.alternatives)

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

    def test_open_terrain_boundary_is_not_a_failure(self):
        qc = {"objects": [{"name": "terrain", "triangles": 100,
                           "non_manifold_edges": 40, "boundary_edges": 40,
                           "loose_vertices": 0, "has_uv": True}],
              "runtime_triangles": 100}
        self.assertTrue(decide(qc, animated=False, references=False,
                               triangle_budget=500, allow_open_mesh=True).technical_pass)
        self.assertFalse(decide(qc, animated=False, references=False,
                                triangle_budget=500).technical_pass)

    def test_200k_triangle_limit(self):
        with self.assertRaises(ValueError):
            AssetSpec("over_limit", "dragon", "creature",
                      target_triangles=200001).validate()
        AssetSpec("within_limit", "dragon", "creature",
                  target_triangles=200000).validate()

    def test_fragmented_creature_fails_even_if_watertight(self):
        qc = {"objects": [{"name": "dragon", "triangles": 15000,
                "connected_components": 19,
                "largest_component_triangle_fraction": 0.72,
                "loose_vertices": 0, "non_manifold_edges": 0,
                "has_uv": True}], "runtime_triangles": 15000,
              "clay_render_files": ["clay_front.png", "clay_side.png",
                                    "clay_three_quarter.png"]}
        d = decide(qc, animated=True, references=True,
                   triangle_budget=200000, require_connected=True,
                   require_png=True)
        self.assertFalse(d.technical_pass)
        self.assertTrue(any("disconnected" in x for x in d.failures))
        self.assertFalse(d.visual_approved)

    def test_missing_clay_renders_fails(self):
        qc = {"objects": [{"name": "dragon", "triangles": 15000,
                "connected_components": 1,
                "largest_component_triangle_fraction": 1.0,
                "loose_vertices": 0, "non_manifold_edges": 0,
                "has_uv": True}], "runtime_triangles": 15000}
        self.assertFalse(decide(qc, animated=True, references=True,
                triangle_budget=200000, require_connected=True,
                require_png=True).technical_pass)

    def test_qc_rejects_bad_mesh(self):
        qc = {"objects": [{"name": "bad", "triangles": 20, "non_manifold_edges": 5,
                            "loose_vertices": 0, "has_uv": False}],
              "runtime_triangles": 20}
        self.assertFalse(decide(qc, animated=True, references=False, triangle_budget=100).technical_pass)


if __name__ == "__main__":
    unittest.main()

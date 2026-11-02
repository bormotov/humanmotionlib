# SPDX-License-Identifier: Apache-2.0
"""Host validation tests for the first-class character registry."""
import unittest
from unittest import mock
from copy import deepcopy

from humanmotionlib import characters


class CharacterRegistryTests(unittest.TestCase):
    def test_registry_and_default_skeleton_are_surface_lazy(self):
        with mock.patch.object(characters, "_load_yaml", wraps=characters._load_yaml) as load:
            selected = characters.resolve_character_selection(("skeleton",), profile_id="adult-reference-v1")
        self.assertEqual([row["id"] for row in selected], ["skeleton"])
        self.assertEqual(selected[0]["renderer_kind"], "skeletal")
        self.assertNotIn("template", selected[0])
        self.assertFalse(any("templates/" in call.args[0] for call in load.call_args_list))
        self.assertFalse(any("appearances/" in call.args[0] for call in load.call_args_list))

    def test_selection_is_normalized_to_registry_order(self):
        selected = characters.resolve_character_selection(("female", "skeleton", "male"),
                                                           profile_id="adult-reference-v1")
        self.assertEqual([row["id"] for row in selected], ["skeleton", "male", "female"])
        self.assertEqual(len(selected[0]["source_hashes"]), 4)
        self.assertEqual(len(selected[1]["source_hashes"]), 9)
        self.assertEqual(len(selected[2]["source_hashes"]), 9)

    def test_complete_registry_sources_validate(self):
        selected = characters.validate_character_sources()
        self.assertEqual([row["id"] for row in selected], ["skeleton", "male", "female"])
        self.assertTrue(selected[1]["source_hashes"])
        self.assertTrue(selected[2]["source_hashes"])

    def test_character_documentation_covers_schema_units_simplifications_and_future_limits(self):
        from pathlib import Path
        document = (Path(__file__).resolve().parents[1] / "docs/character-models.md").read_text()
        for required in (
            "registry.yaml", "definitions/", "template_revision", "binding_revision",
            "expected_rest_contract_sha256", "rest_contract_structures", "torso_radii_delta_h", "radius_h",
            "stature_m", "not a welded watertight body or a simulation mesh",
            "binding identity", "no runtime body-type selector",
            "Future alternate skeletal proportions and body-type presets are unsupported",
            "CharacterSurface.<id>", "CharacterSurface.male", "CharacterSurface.female",
            "Overlapping caps at mannequin junctions are intentional",
            "images=False, render_only=False", "render_only=True` build skips evaluated geometry",
            "It produces images only when `images=True`; `images=False` produces no images",
        ):
            with self.subTest(required=required):
                self.assertIn(required, document)
        self.assertNotIn("mocap-quality anatomy", document.lower())

    def test_unknown_duplicate_and_incompatible_ids_fail(self):
        for ids in (("ghost",), ("skeleton", "skeleton")):
            with self.subTest(ids=ids), self.assertRaises(characters.CharacterSourceError):
                characters.resolve_character_selection(ids, profile_id="adult-reference-v1")
        with self.assertRaises(characters.CharacterSourceError):
            characters.resolve_character_selection(("male",), profile_id="other-profile")

    def test_rest_digest_is_independent_of_mapping_key_order(self):
        import yaml
        from humanmotionlib.package_resources import read_text
        profile = yaml.safe_load(read_text("rig/profiles/adult-reference-v1.yaml"))
        template = yaml.safe_load(read_text("characters/templates/exercise-mannequin-v1.yaml"))
        expected = template["expected_rest_contract_sha256"]
        self.assertEqual(characters.rest_contract_digest(profile, template), expected)
        reversed_profile = dict(reversed(list(profile.items())))
        self.assertEqual(characters.rest_contract_digest(reversed_profile, template), expected)

    def test_rest_binding_digest_is_request_stature_independent(self):
        """A render stature scales geometry, never the reusable rig bind."""
        import tempfile
        import yaml
        from pathlib import Path
        from humanmotionlib import api
        from humanmotionlib.package_resources import read_text
        profile = yaml.safe_load(read_text("rig/profiles/adult-reference-v1.yaml"))
        template = yaml.safe_load(read_text("characters/templates/exercise-mannequin-v1.yaml"))
        digest = characters.rest_contract_digest(profile, template)
        self.assertEqual(digest, template["expected_rest_contract_sha256"])
        # Exercise actual preparations at all dossier statures. Their selected
        # render stature must not alter the canonical, unscaled binding source.
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "build").mkdir()
            for stature_m, suffix in ((1.50, "h150"), (1.70, "h170"), (1.90, "h190")):
                result = api.prepare(
                    workspace=workspace,
                    output=f"build/character-digest-test_r1_test_try-1_{suffix}/input.json",
                    stature=stature_m, fixtures=("neutral",), bpms=(60,),
                )
                with self.subTest(stature_m=stature_m):
                    self.assertEqual(result.stature_m, stature_m)
                    self.assertEqual(characters.rest_contract_digest(profile, template), digest)

        # Conversely, changing an actual unscaled rest transform must renew
        # the binding rather than being hidden as a stature variation.
        changed = deepcopy(profile)
        row = next(item for item in changed["structures"] if item["id"] == "humerus.R")
        row["rest_translation_m"][0] += 0.001
        self.assertNotEqual(characters.rest_contract_digest(changed, template), digest)

    def test_rest_digest_rejects_unresolved_and_cyclic_parent_closures(self):
        template = {"rest_contract_structures": ["child"]}
        base = {"id": "adult-reference-v1", "structures": [
            {"id": "child", "parent": "parent", "origin_m": [0, 0, 0],
             "basis": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
             "rest_translation_m": [0, 0, 0], "rest_orientation": [1, 0, 0, 0],
             "attachments": []},
            {"id": "parent", "parent": None, "origin_m": [0, 0, 0],
             "basis": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
             "rest_translation_m": [0, 0, 0], "rest_orientation": [1, 0, 0, 0],
             "attachments": []},
        ]}
        self.assertEqual(len(characters.rest_contract_digest(base, template)), 64)
        unresolved = {**base, "structures": [dict(base["structures"][0], parent="missing")]}
        with self.assertRaisesRegex(characters.CharacterSourceError, "unresolved"):
            characters.rest_contract_digest(unresolved, template)
        cyclic_rows = [dict(row) for row in base["structures"]]
        cyclic_rows[1]["parent"] = "child"
        with self.assertRaisesRegex(characters.CharacterSourceError, "cycle"):
            characters.rest_contract_digest({**base, "structures": cyclic_rows}, template)

    def test_selected_surface_closure_rejects_hostile_schema_provenance_and_bind_values(self):
        original_loader = characters._load_yaml

        def selected_with_mutation(target, mutate):
            def load(logical):
                document = deepcopy(original_loader(logical))
                if logical == target:
                    mutate(document)
                return document
            with mock.patch.object(characters, "_load_yaml", side_effect=load):
                character_id = "female" if "female-v1" in target else "male"
                return characters.resolve_character_selection((character_id,), profile_id="adult-reference-v1")

        cases = (
            ("characters/appearances/male-v1.yaml",
             lambda doc: doc.update(unexpected_source_field=True), "Additional properties"),
            ("characters/appearances/male-v1.yaml",
             lambda doc: doc["radius_scales"].update(arm=-0.1), "less than or equal"),
            ("characters/appearances/male-v1.yaml",
             lambda doc: doc["radius_scales"].update(arm=float("nan")), "nonfinite"),
            ("characters/appearances/female-v1.yaml",
             lambda doc: doc["torso_radii_delta_h"].pop(), "short"),
            ("characters/appearances/female-v1.yaml",
             lambda doc: doc["torso_radii_delta_h"].__setitem__(0, [0.0]), "short"),
            ("characters/appearances/female-v1.yaml",
             lambda doc: doc["torso_radii_delta_h"].__setitem__(0, [0.0, 0.0, 0.0]), "long"),
            ("characters/appearances/male-v1.yaml",
             lambda doc: doc["torso_radii_delta_h"].__setitem__(0, [0.001, 0.0]), "was expected"),
            ("characters/appearances/female-v1.yaml",
             lambda doc: doc.update(torso_radii_h=[[.08, .05]] * 10), "Additional properties"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["components"][0]["control_rings"][0].update(
                 radii_source="appearance.torso_radii_h"), "not valid under any"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["components"][0]["control_rings"][0].update(radius_h=[0.0, .05]),
             "not valid under any"),
            ("characters/appearances/male-v1.yaml",
             lambda doc: doc["provenance"].update(license="CC-BY-NC-4.0"), "CC-BY-4.0"),
            ("characters/definitions/male.yaml",
             lambda doc: doc.pop("provenance"), "required property"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc.update(expected_rest_contract_sha256="0" * 64), "stale character binding"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc.update(compatible_profile="other-profile"), "compatible_profile"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["components"][0].update(geometry="python-expression"),
             "not valid under any of the given schemas"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["rest_contract_structures"].__setitem__(0, "missing-carrier"), "unresolved"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["components"][2]["weighting"]["bands"][0].__setitem__("from", "ghost.R"),
             "unresolved carrier"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["components"][2]["weighting"]["bands"][0].__setitem__("from", "toe.2.R.origin"),
             "unresolved carrier"),
            ("characters/templates/exercise-mannequin-v1.yaml",
             lambda doc: doc["components"][2]["weighting"]["bands"][0].__setitem__("from", "metatarsal.2.R"),
             "outside rest-contract binding closure"),
        )
        for logical, mutate, expected in cases:
            with self.subTest(source=logical, expected=expected), self.assertRaisesRegex(
                    characters.CharacterSourceError, expected):
                selected_with_mutation(logical, mutate)

    def test_profile_closure_nonfinite_and_unresolved_rest_fails_before_surface_use(self):
        original_loader = characters._load_yaml
        mutations = (
            lambda doc: next(row for row in doc["structures"] if row["id"] == "humerus.R")
                ["rest_translation_m"].__setitem__(0, float("nan")),
            lambda doc: next(row for row in doc["structures"] if row["id"] == "humerus.R")
                .update(parent="missing-parent"),
        )
        for mutate, expected in zip(mutations, ("nonfinite numeric value", "unresolved")):
            def load(logical):
                document = deepcopy(original_loader(logical))
                if logical == "rig/profiles/adult-reference-v1.yaml":
                    mutate(document)
                return document
            with self.subTest(expected=expected), mock.patch.object(
                    characters, "_load_yaml", side_effect=load), self.assertRaisesRegex(
                        (characters.CharacterSourceError, ValueError), expected):
                characters.resolve_character_selection(("male",), profile_id="adult-reference-v1")

    def test_profile_hierarchy_cycle_is_rejected_in_selected_closure(self):
        original_loader = characters._load_yaml

        def load(logical):
            document = deepcopy(original_loader(logical))
            if logical == "rig/profiles/adult-reference-v1.yaml":
                next(row for row in document["structures"] if row["id"] == "humerus.R")["parent"] = "humerus.R"
            return document

        with mock.patch.object(characters, "_load_yaml", side_effect=load), self.assertRaisesRegex(
                characters.CharacterSourceError, "cycle"):
            characters.resolve_character_selection(("male",), profile_id="adult-reference-v1")

    def test_prepare_and_skeleton_selection_never_parse_surface_template(self):
        import tempfile
        from pathlib import Path
        from humanmotionlib import api

        selected = characters.resolve_character_selection(("skeleton",), profile_id="adult-reference-v1")
        self.assertEqual([row["id"] for row in selected], ["skeleton"])
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "build").mkdir()
            output = "build/character-lazy-test_r1_test_try-1_prepare/input.json"
            with mock.patch.object(characters, "_load_yaml", side_effect=AssertionError(
                    "prepare or skeleton selection parsed a character surface source")) as loader:
                result = api.prepare(workspace=workspace, output=output,
                                     stature=1.70, fixtures=("neutral",), bpms=(60,))
            self.assertTrue(result.prepared_path.is_file())
            loader.assert_not_called()

    def test_source_closure_faults_precede_output_allocation_and_backend_probe(self):
        import tempfile
        from pathlib import Path
        from humanmotionlib import api

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "build").mkdir()
            prepared = api.prepare(workspace=workspace,
                                   output="build/character-preflight-test_r1_test_try-1_prepare/input.json",
                                   fixtures=("neutral",), bpms=(60,))
            original_loader = characters._load_yaml
            faults = (
                ("characters/templates/exercise-mannequin-v1.yaml",
                 lambda doc: doc["components"][2]["weighting"]["bands"][0].__setitem__("from", "ghost.R")),
                ("characters/definitions/male.yaml", lambda doc: doc.pop("provenance")),
                ("characters/templates/exercise-mannequin-v1.yaml",
                 lambda doc: doc.update(expected_rest_contract_sha256="0" * 64)),
            )
            for index, (target, mutate) in enumerate(faults):
                output = f"build/character-preflight-test_r1_test_try-1_fault-{index}"

                def load(logical):
                    document = deepcopy(original_loader(logical))
                    if logical == target:
                        mutate(document)
                    return document

                with (self.subTest(target=target, index=index),
                      mock.patch.object(characters, "_load_yaml", side_effect=load),
                      mock.patch.object(api.run_blender, "run") as backend,
                      self.assertRaises(api.GenerationError) as caught):
                    api.render(prepared, workspace=workspace, output=output, characters=("male",))
                self.assertEqual(caught.exception.code, "invalid-request")
                self.assertFalse((workspace / output).exists())
                backend.assert_not_called()

    def test_nonpositive_effective_torso_delta_fails_before_output_or_backend(self):
        import tempfile
        from pathlib import Path
        from humanmotionlib import api

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "build").mkdir()
            prepared = api.prepare(workspace=workspace,
                                   output="build/character-effective-radius-test_r1_test_try-1_prepare/input.json",
                                   fixtures=("neutral",), bpms=(60,))
            original_loader = characters._load_yaml

            def load(logical):
                document = deepcopy(original_loader(logical))
                if logical == "characters/appearances/female-v1.yaml":
                    document["torso_radii_delta_h"][2][0] = -document["torso_radii_delta_h"][2][0] - .098
                return document

            output = "build/character-effective-radius-test_r1_test_try-1_render"
            with (mock.patch.object(characters, "_load_yaml", side_effect=load),
                  mock.patch.object(api.run_blender, "run") as backend,
                  self.assertRaises(api.GenerationError) as caught):
                api.render(prepared, workspace=workspace, output=output, characters=("female",))
            self.assertEqual(caught.exception.code, "invalid-request")
            self.assertIn("effective torso radius", str(caught.exception))
            self.assertFalse((workspace / output).exists())
            backend.assert_not_called()


if __name__ == "__main__":
    unittest.main()

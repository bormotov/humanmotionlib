# SPDX-License-Identifier: Apache-2.0
"""Propagation checks mutate only disposable source copies."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from humanmotionlib.character_surface import expand_surface
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib import characters


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "rig/profiles/adult-reference-v1.yaml"
TEMPLATE_PATH = ROOT / "characters/templates/exercise-mannequin-v1.yaml"
MALE_PATH = ROOT / "characters/appearances/male-v1.yaml"
FEMALE_PATH = ROOT / "characters/appearances/female-v1.yaml"


def _read(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _copy_source(temp_root, relative):
    target = Path(temp_root) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (ROOT / relative).read_bytes()
    target.write_bytes(payload)
    return target


class CharacterPropagationTests(unittest.TestCase):
    def _surface_inputs(self):
        return (_read(PROFILE_PATH), _read(TEMPLATE_PATH), _read(MALE_PATH), _read(FEMALE_PATH))

    def test_common_arm_raise_key_changes_one_shared_preparation_for_all_ids(self):
        before_hash = hashlib.sha256((ROOT / "rig/diagnostics/arm-raise.yaml").read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="hml-character-motion-copy-") as temp:
            fixture_path = _copy_source(temp, "rig/diagnostics/arm-raise.yaml")
            original_fixture = yaml.safe_load(fixture_path.read_text())
            changed_fixture = deepcopy(original_fixture)
            changed_key = next(key for track in changed_fixture["tracks"]
                               if track["channel"] == "shoulder.R.elevation"
                               for key in track["keys"] if key["beat"] == 2)
            changed_key["value"] = 150
            fixture_path.write_text(yaml.safe_dump(changed_fixture, sort_keys=False), encoding="utf-8")
            sources = {
                "profile": _read(PROFILE_PATH),
                "mobility": _read(ROOT / "rig/mobility/adult-reference-v1.yaml"),
                "body-groups": _read(ROOT / "rig/body-groups.yaml"),
                "diagnostics": [_read(ROOT / "rig/diagnostics/neutral.yaml"),
                                yaml.safe_load(fixture_path.read_text(encoding="utf-8"))],
            }
            evaluator = DiagnosticEvaluator(sources)
            changed = evaluator.evaluate("arm-raise", 2.0)
            original_sources = deepcopy(sources)
            original_sources["diagnostics"][1] = original_fixture
            unmodified = DiagnosticEvaluator(original_sources).evaluate("arm-raise", 2.0)
            self.assertEqual(changed["actions"]["shoulder.R.elevation"], 150)
            self.assertEqual(unmodified["actions"]["shoulder.R.elevation"], 160)
            self.assertNotEqual(changed["frames"]["wrist.R"], unmodified["frames"]["wrist.R"])
            # Render selection consumes one prepared sample for every registered
            # ID; no character descriptor owns or rewrites movement frames.
            shared_sample = {"frames": changed["frames"], "actions": changed["actions"],
                             "contacts": changed["contacts"], "beat": 2.0}
            selected = {identifier: shared_sample for identifier in ("skeleton", "male", "female")}
            self.assertEqual(list(selected), ["skeleton", "male", "female"])
            self.assertTrue(all(selected[identifier] is shared_sample for identifier in selected))
        self.assertEqual(before_hash, hashlib.sha256((ROOT / "rig/diagnostics/arm-raise.yaml").read_bytes()).hexdigest())

    def test_shared_arm_radius_propagates_to_both_appearances_only(self):
        profile, template, male, female = self._surface_inputs()
        profile_before = deepcopy(profile)
        male_before = expand_surface(profile, template, male, 1.70)
        female_before = expand_surface(profile, template, female, 1.70)
        changed_template = deepcopy(template)
        # The third authored arm ring is in the shoulder-to-elbow span; change
        # its anterior radius by the specified 0.001H in the disposable copy.
        changed_template["components"][2]["control_rings"][2]["radius_h"][0] += 0.001
        with tempfile.TemporaryDirectory(prefix="hml-character-radius-copy-") as temp:
            copy_path = Path(temp) / "exercise-mannequin-v1.yaml"
            copy_path.write_text(yaml.safe_dump(changed_template, sort_keys=False), encoding="utf-8")
            isolated_template = yaml.safe_load(copy_path.read_text(encoding="utf-8"))
            male_after = expand_surface(profile, isolated_template, male, 1.70)
            female_after = expand_surface(profile, isolated_template, female, 1.70)
        for before, after, scale in ((male_before, male_after, 1.0),
                                     (female_before, female_after, female["radius_scales"]["arm"])):
            old = before["components"][2]["vertices_m"][8*32]
            new = after["components"][2]["vertices_m"][8*32]
            self.assertAlmostEqual(sum((new[i]-old[i])**2 for i in range(3))**0.5,
                                   0.001*1.70*scale, delta=1e-10)
        self.assertEqual(profile, profile_before)
        self.assertEqual(male_before["components"][0], male_after["components"][0])
        self.assertEqual(female_before["components"][0], female_after["components"][0])
        self.assertNotEqual(male_before["surface_sha256"], male_after["surface_sha256"])
        self.assertNotEqual(female_before["surface_sha256"], female_after["surface_sha256"])

    def test_female_waist_edit_isolated_to_female_surface(self):
        profile, template, male, female = self._surface_inputs()
        male_before = expand_surface(profile, template, male, 1.70)
        female_before = expand_surface(profile, template, female, 1.70)
        changed_female = deepcopy(female)
        changed_female["torso_radii_delta_h"][3][0] += 0.001
        with tempfile.TemporaryDirectory(prefix="hml-character-waist-copy-") as temp:
            copy_path = Path(temp) / "female-v1.yaml"
            copy_path.write_text(yaml.safe_dump(changed_female, sort_keys=False), encoding="utf-8")
            isolated_female = yaml.safe_load(copy_path.read_text(encoding="utf-8"))
            male_after = expand_surface(profile, template, male, 1.70)
            female_after = expand_surface(profile, template, isolated_female, 1.70)
        self.assertEqual(male_before, male_after)
        self.assertNotEqual(female_before["surface_sha256"], female_after["surface_sha256"])
        torso = female_before["components"][0]
        changed_torso = female_after["components"][0]
        # Control ring 3 is inserted every four generated rings.
        vertex_index = 3*4*32
        self.assertAlmostEqual(changed_torso["vertices_m"][vertex_index][0]
                               - torso["vertices_m"][vertex_index][0], 0.001*1.70, delta=1e-12)
        self.assertEqual(profile["stature_m"], 1.70)

    def test_stale_shoulder_bind_rejects_both_surfaces_but_not_skeleton(self):
        profile, template, male, female = self._surface_inputs()
        registry = _read(ROOT / "characters/registry.yaml")
        definitions = {identifier: _read(ROOT / f"characters/definitions/{identifier}.yaml")
                       for identifier in ("skeleton", "male", "female")}
        original = {"characters/registry.yaml":registry,
                    "characters/definitions/skeleton.yaml":definitions["skeleton"],
                    "characters/definitions/male.yaml":definitions["male"],
                    "characters/definitions/female.yaml":definitions["female"],
                    "characters/templates/exercise-mannequin-v1.yaml":template,
                    "characters/appearances/male-v1.yaml":male,
                    "characters/appearances/female-v1.yaml":female,
                    "schema/character-registry.schema.json":_read(ROOT / "schema/character-registry.schema.json"),
                    "schema/character-definition.schema.json":_read(ROOT / "schema/character-definition.schema.json"),
                    "schema/character-template.schema.json":_read(ROOT / "schema/character-template.schema.json"),
                    "schema/character-appearance.schema.json":_read(ROOT / "schema/character-appearance.schema.json"),
                    "rig/profiles/adult-reference-v1.yaml":profile}
        with tempfile.TemporaryDirectory(prefix="hml-character-bind-copy-") as temp:
            source_root = Path(temp)
            for logical, document in original.items():
                path = source_root / logical
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            stale_profile = deepcopy(profile)
            structure = next(row for row in stale_profile["structures"] if row["id"] == "humerus.R")
            structure["rest_translation_m"][0] += 0.0001
            profile_path = source_root / "rig/profiles/adult-reference-v1.yaml"
            profile_path.write_text(yaml.safe_dump(stale_profile, sort_keys=False), encoding="utf-8")
            documents = {logical: yaml.safe_load((source_root / logical).read_text(encoding="utf-8"))
                         for logical in original}
            documents["rig/profiles/adult-reference-v1.yaml"] = yaml.safe_load(profile_path.read_text())
            def loader(logical):
                return deepcopy(documents[logical])
            def read_copy_bytes(logical):
                return (source_root / logical).read_bytes()
            with patch.object(characters, "_load_yaml", side_effect=loader), \
                    patch.object(characters, "read_bytes", side_effect=read_copy_bytes):
                skeleton = characters.resolve_character_selection(("skeleton",), profile_id="adult-reference-v1")
                self.assertEqual(skeleton[0]["id"], "skeleton")
                for identifier in ("male", "female"):
                    with self.subTest(character=identifier), self.assertRaisesRegex(ValueError, "stale character binding"):
                        characters.resolve_character_selection((identifier,), profile_id="adult-reference-v1")


if __name__ == "__main__":
    unittest.main()

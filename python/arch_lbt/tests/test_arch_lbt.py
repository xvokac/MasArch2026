from __future__ import annotations

import unittest
from pathlib import Path
from dataclasses import replace

import numpy as np

from arch_lbt import (
    check_global_equilibrium,
    build_model,
    lbt_input_from_melb,
    diagnose_equilibrium_only,
    diagnose_moment_only,
    format_model_report,
    read_arch_lbt_input,
    read_model,
    solve_infinite_strength_lower_bound,
    solve_parabolic_interaction_lower_bound,
    write_arch_lbt_input,
)


ROOT = Path(__file__).resolve().parents[2]


class ArchLBTModelTest(unittest.TestCase):
    def test_reads_melb_input_and_prepares_geometry(self) -> None:
        model = read_model(ROOT / "klenba_1.in")
        self.assertEqual(model.block_count, 25)
        self.assertEqual(model.joint_count, 26)
        self.assertEqual(model.intrados.shape, (26, 2))
        self.assertEqual(model.extrados.shape, (26, 2))
        self.assertGreater(model.load_summary.total_vertical, 0.0)

    def test_supported_geometry_codes_match_gui_choices(self) -> None:
        source_model = read_model(ROOT / "klenba_1.in")
        lbt_data = lbt_input_from_melb(source_model.input, friction_coefficient=0.1, path=ROOT / "tmp_geom_lbt.in")
        for geom_code in (1, 2):
            model = build_model(replace(lbt_data, geom_code=geom_code))
            self.assertEqual(model.block_count, 25)
            self.assertEqual(model.intrados.shape, (26, 2))

    def test_horizontal_extrados_mode_builds_flat_extrados(self) -> None:
        source_model = read_model(ROOT / "klenba_1.in")
        lbt_data = lbt_input_from_melb(source_model.input, friction_coefficient=0.1, path=ROOT / "tmp_horizontal_lbt.in")
        model = build_model(replace(lbt_data, extrados_mode="horizontal"))
        self.assertEqual(model.extrados_mode, "horizontal")
        self.assertTrue(np.allclose(model.extrados[:, 1], model.extrados[0, 1]))
        result = solve_parabolic_interaction_lower_bound(model)
        self.assertTrue(result.success)
        self.assertGreater(result.final_state.normal_forces.max(), 0.0)

    def test_horizontal_radial_joints_mode_builds_wider_flat_extrados(self) -> None:
        source_model = read_model(ROOT / "klenba_1.in")
        lbt_data = lbt_input_from_melb(source_model.input, friction_coefficient=0.1, path=ROOT / "tmp_horizontal_radial_lbt.in")
        model = build_model(replace(lbt_data, extrados_mode="horizontal_width_radial_joints"))
        self.assertEqual(model.extrados_mode, "horizontal_width_radial_joints")
        self.assertTrue(np.allclose(model.extrados[:, 1], model.extrados[0, 1]))
        self.assertLess(model.extrados[0, 0], model.intrados[0, 0])
        self.assertGreater(model.extrados[-1, 0], model.intrados[-1, 0])
        diagnostic = diagnose_equilibrium_only(model)
        self.assertTrue(diagnostic.success)

    def test_lbt_file_preserves_horizontal_extrados_mode(self) -> None:
        path = ROOT / "klenba02_1_lbt.in"
        if not path.exists():
            self.skipTest("klenba02_1_lbt.in is not available")
        data = read_arch_lbt_input(path)
        self.assertEqual(data.extrados_mode, "horizontal")
        model = read_model(path)
        self.assertEqual(model.extrados_mode, "horizontal")

    def test_solves_infinite_strength_lower_bound(self) -> None:
        model = read_model(ROOT / "klenba_1.in")
        result = solve_infinite_strength_lower_bound(model)
        self.assertGreaterEqual(result.load_factor, 0.0)
        self.assertEqual(result.final_state.normal_forces.shape, (model.joint_count,))
        self.assertEqual(result.final_state.moments.shape, (model.joint_count,))

    def test_equilibrium_only_diagnostic(self) -> None:
        model = read_model(ROOT / "klenba_1.in")
        diagnostic = diagnose_equilibrium_only(model)
        self.assertTrue(diagnostic.success)
        self.assertEqual(diagnostic.variable_count, 4)
        self.assertEqual(diagnostic.joint_count, model.joint_count)

    def test_moment_only_diagnostic_returns_status(self) -> None:
        model = read_model(ROOT / "klenba_1.in")
        diagnostic = diagnose_moment_only(model)
        self.assertGreaterEqual(diagnostic.load_factor, 0.0)
        self.assertEqual(diagnostic.final_state.moments.shape, (model.joint_count,))

    def test_report_contains_lower_bound_sections(self) -> None:
        report = format_model_report(read_model(ROOT / "klenba_1.in"))
        self.assertIn("ArchLBT prepared model", report)
        self.assertIn("Lower-bound skeleton", report)
        self.assertIn("lambda_max", report)
        self.assertIn("statically admissible", report)

    def test_parabolic_interaction_result_is_bounded_by_compression_limit(self) -> None:
        model = read_model(ROOT / "klenba_1.in")
        result = solve_parabolic_interaction_lower_bound(model)
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.load_factor, 0.0)
        self.assertGreaterEqual(result.final_state.normal_forces.min(), -1e-8)
        self.assertLessEqual(result.final_state.normal_forces.max(), model.input.d_sigma * model.arch_width * model.input.thickness + 1e-8)

    def test_lbt_width_scales_loads_and_compression_limit(self) -> None:
        base_model = read_model(ROOT / "klenba_1.in")
        lbt_data = lbt_input_from_melb(base_model.input, friction_coefficient=0.1, path=ROOT / "klenba_1_lbt.in")
        wide_model = build_model(replace(lbt_data, arch_width=2.0))
        self.assertAlmostEqual(wide_model.arch_width, 2.0)
        self.assertAlmostEqual(wide_model.load_summary.permanent_vertical, 2.0 * base_model.load_summary.permanent_vertical)
        self.assertAlmostEqual(wide_model.load_summary.fill_vertical, 2.0 * base_model.load_summary.fill_vertical)
        self.assertAlmostEqual(wide_model.load_summary.variable_vertical, base_model.load_summary.variable_vertical)
        result = solve_parabolic_interaction_lower_bound(wide_model)
        self.assertLessEqual(result.final_state.normal_forces.max(), wide_model.input.d_sigma * wide_model.arch_width * wide_model.section_depths.max() + 1e-8)

    def test_global_equilibrium_residual_is_near_zero(self) -> None:
        model = read_model(ROOT / "klenba_1.in")
        result = solve_parabolic_interaction_lower_bound(model)
        check = check_global_equilibrium(model, result)
        self.assertAlmostEqual(check.residual_force_x, 0.0, places=9)
        self.assertAlmostEqual(check.residual_force_y, 0.0, places=9)
        self.assertAlmostEqual(check.residual_moment, 0.0, places=9)

    def test_lbt_input_roundtrip_and_solve(self) -> None:
        source_model = read_model(ROOT / "klenba_1.in")
        lbt_data = lbt_input_from_melb(source_model.input, friction_coefficient=0.1, path=ROOT / "tmp_test_lbt.in")
        tmp_path = ROOT / "tmp_test_lbt.in"
        try:
            write_arch_lbt_input(lbt_data, tmp_path)
            parsed = read_arch_lbt_input(tmp_path)
            self.assertEqual(parsed.block_count, source_model.block_count)
            self.assertAlmostEqual(parsed.friction_coefficient, 0.1)
            model = read_model(tmp_path)
            result = solve_parabolic_interaction_lower_bound(model)
            self.assertTrue(result.success)
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

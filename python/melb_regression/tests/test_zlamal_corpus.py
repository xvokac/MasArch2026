from __future__ import annotations

from collections import Counter
from dataclasses import replace
import unittest
from pathlib import Path

from melb_regression import (
    build_linprog_model,
    format_melb_input,
    load_zlamal_cases,
    LinprogResult,
    MelbSolveError,
    prepare_melb_input,
    read_ab_dump,
    read_detail_txt,
    read_melb_input,
    read_simplex_bytes,
    read_simplex_dump,
    write_melb_outputs,
    solve_melb_iterations,
    solve_linprog_model,
)


ORIGINAL = Path(r"D:\Documents\2026\MASARCH2026\masarch")
MELBOURNE = Path(r"D:\Documents\2026\MASARCH2026\Melbourne")


class ZlamalCorpusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_zlamal_cases(ORIGINAL)

    def test_case_count_and_method_distribution(self) -> None:
        self.assertEqual(len(self.cases), 112)
        self.assertEqual(
            Counter(case.d_code for case in self.cases),
            {0: 14, 1: 14, 2: 14, 3: 14, 4: 56},
        )

    def test_common_input_variants(self) -> None:
        self.assertEqual(Counter(case.geom_code for case in self.cases), {1: 112})
        self.assertEqual(Counter(case.q_code for case in self.cases), {0: 112})
        self.assertEqual(Counter(case.k_code for case in self.cases), {0: 112})
        self.assertEqual(Counter(case.block_count for case in self.cases), {40: 112})

    def test_preserved_results_are_parseable(self) -> None:
        with_result = [case for case in self.cases if case.result is not None]
        self.assertEqual(len(with_result), 106)
        self.assertEqual(Counter(case.result.icase for case in with_result), {0: 106})

    def test_reference_lambdas(self) -> None:
        by_name = {case.relative_name: case for case in self.cases}
        self.assertAlmostEqual(by_name[r"zlamal0.in"].result.load_factor, 4.720544)
        self.assertAlmostEqual(by_name[r"zlamal0\zlamal0_12.in"].result.load_factor, 21.375492)
        self.assertAlmostEqual(by_name[r"zlamal1\zlamal1_12.in"].result.load_factor, 21.375492)
        self.assertAlmostEqual(by_name[r"zlamal7\zlamal7_12.in"].result.load_factor, 3.362883)

    def test_reference_local_deformations(self) -> None:
        by_name = {case.relative_name: case for case in self.cases}
        result = by_name[r"zlamal0\zlamal0_1.in"].result
        self.assertAlmostEqual(result.load_factor, 9.158882)
        self.assertEqual(
            [(item.variable_index, item.joint_index, item.side) for item in result.local_deformations],
            [(1, 0, "int"), (16, 7, "ext"), (51, 25, "int"), (82, 40, "ext")],
        )
        self.assertEqual(
            [round(item.value, 6) for item in result.local_deformations],
            [5.000002, 8.384995, 6.77813, 3.393136],
        )

    def test_reference_simplex_dump_shape(self) -> None:
        dump = read_simplex_dump(ORIGINAL / "zlamal0" / "zlamal0_1.sim")
        self.assertEqual((dump.first_header, dump.second_header, dump.third_header), (164, 4, -1))
        self.assertEqual(dump.raw_cell_count, 828)
        self.assertEqual(dump.as_rows_by_header.shape, (5, 165))
        self.assertEqual(dump.as_constraints_by_header.shape, (165, 5))
        self.assertEqual(dump.trailing_ints, (0, 0, 3))
        self.assertEqual(dump.nr_variable_count, 164)
        self.assertEqual(dump.nr_constraint_count, 3)

    def test_reference_ab_dump_shape_and_row_groups(self) -> None:
        dump = read_ab_dump(ORIGINAL / "zlamal0" / "zlamal0_1.AB", block_count=40)
        self.assertEqual(dump.matrix.shape, (164, 123))
        self.assertEqual(dump.phi_rows.shape, (82, 123))
        self.assertEqual(dump.sliding_rows.shape, (82, 123))

        first_phi_int, first_phi_ext = dump.phi_row_pair(0)
        self.assertEqual(round(first_phi_int[2], 6), 1.0)
        self.assertEqual(round(first_phi_ext[2], 6), -1.0)
        self.assertEqual(round(first_phi_int[0], 6), 0.03625)
        self.assertEqual(round(first_phi_int[1], 6), -0.062787)

        last_phi_pair = dump.phi_row_pair(40)
        self.assertEqual(sum(abs(value) > 1e-12 for value in last_phi_pair[1]), 3)

        first_sliding_pair = dump.sliding_row_pair(0)
        self.assertEqual(sum(abs(value) > 1e-12 for value in first_sliding_pair[0]), 82)

    def test_ab_dump_size_depends_on_block_count(self) -> None:
        dump = read_ab_dump(ORIGINAL / "AB.tmp", block_count=25)
        self.assertEqual(dump.matrix.shape, (104, 78))

    def test_reference_detail_txt_tables_and_result(self) -> None:
        detail = read_detail_txt(ORIGINAL / "zlamal0" / "zlamal0_1.txt")
        self.assertEqual(detail.input_name, "zlamal0_1.in")
        self.assertEqual(detail.block_count, 40)
        self.assertEqual(detail.joint_count, 41)

        self.assertEqual(detail.intrados_extrados.shape, (41, 4))
        self.assertEqual(detail.masonry_weights.shape, (40, 3))
        self.assertEqual(detail.fill_weights.shape, (40, 4))
        self.assertEqual(detail.external_loads.shape, (40, 3))
        self.assertEqual(detail.local_coordinates.shape, (41, 4))
        self.assertEqual(detail.transformed_masonry.shape, (41, 3))
        self.assertEqual(detail.transformed_fill.shape, (41, 3))
        self.assertEqual(detail.transformed_external.shape, (41, 3))

        self.assertAlmostEqual(detail.intrados_extrados[20, 0], 1.23625)
        self.assertAlmostEqual(detail.external_loads[6, 2], 1.0)
        self.assertAlmostEqual(detail.transformed_external[6, 1], 1.0)
        self.assertAlmostEqual(detail.transformed_external[6, 2], -0.032555)
        self.assertAlmostEqual(detail.result.load_factor, 9.158882)
        self.assertEqual(len(detail.result.joint_indices), 41)
        self.assertAlmostEqual(detail.result.normal_forces[0], 14.176798)
        self.assertAlmostEqual(detail.result.normal_distances[-1], 0.0)
        self.assertAlmostEqual(detail.result.shear_forces[-1], 2.050243)

    def test_ab_transforms_detail_loads_to_simplex_rows(self) -> None:
        root = ORIGINAL / "zlamal0"
        detail = read_detail_txt(root / "zlamal0_1.txt")
        ab = read_ab_dump(root / "zlamal0_1.AB", block_count=detail.block_count)
        simplex = read_simplex_dump(root / "zlamal0_1.sim").as_rows_by_header

        permanent = detail.transformed_masonry + detail.transformed_fill
        variable = detail.transformed_external
        permanent_constraints = ab.transform_joint_loads(permanent)
        variable_constraints = ab.transform_joint_loads(variable)

        self.assertLess(max(abs(simplex[0, : 4 * detail.joint_count] + permanent_constraints)), 1e-5)
        self.assertLess(
            max(abs(simplex[1, : 4 * detail.joint_count - 1] - variable_constraints[1:])),
            1e-6,
        )

    def test_simplex_objective_reproduces_historical_load_factor(self) -> None:
        root = ORIGINAL / "zlamal0"
        detail = read_detail_txt(root / "zlamal0_1.txt")
        simplex = read_simplex_dump(root / "zlamal0_1.sim")

        mechanism = [0.0] * simplex.nr_variable_count
        for item in detail.result.local_deformations:
            mechanism[item.variable_index - 1] = item.value

        load_factor = simplex.objective_coefficients @ mechanism
        self.assertAlmostEqual(load_factor, detail.result.load_factor, delta=2e-5)

    def test_scipy_linprog_reproduces_reference_solution(self) -> None:
        root = ORIGINAL / "zlamal0"
        detail = read_detail_txt(root / "zlamal0_1.txt")
        ab = read_ab_dump(root / "zlamal0_1.AB", block_count=detail.block_count)
        simplex = read_simplex_dump(root / "zlamal0_1.sim")

        model = build_linprog_model(detail, ab, simplex)
        result = solve_linprog_model(model)

        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.load_factor, detail.result.load_factor, delta=3e-5)
        active = [index + 1 for index, value in enumerate(result.mechanism) if value > 1e-5]
        self.assertEqual(active, [1, 16, 51, 82])
        for item in detail.result.local_deformations:
            self.assertAlmostEqual(result.mechanism[item.variable_index - 1], item.value, delta=1e-5)

    def test_detail_txt_parser_handles_pokus_out(self) -> None:
        detail = read_detail_txt(ORIGINAL / "pokus_out")
        self.assertEqual(detail.input_name, "pokus_in")
        self.assertEqual(detail.block_count, 25)
        self.assertEqual(detail.intrados_extrados.shape, (26, 4))
        self.assertEqual(detail.masonry_weights.shape, (25, 3))
        self.assertEqual(detail.transformed_fill.shape, (26, 3))
        self.assertAlmostEqual(detail.fill_weights[0, 0], 1.298961)
        self.assertAlmostEqual(detail.transformed_fill[0, 1], 1.298961)
        self.assertAlmostEqual(detail.result.load_factor, 5.979780)

    def test_detail_txt_parser_keeps_iteration_result_blocks(self) -> None:
        detail = read_detail_txt(ORIGINAL / "zlamal1" / "zlamal1_1.txt")
        self.assertEqual(len(detail.result_summaries), 3)
        self.assertAlmostEqual(detail.result_summaries[0].load_factor, 9.158882)
        self.assertAlmostEqual(detail.final_result_summary.load_factor, 8.765233)
        self.assertEqual(
            [item.variable_index for item in detail.final_result_summary.local_deformations],
            [1, 16, 51, 82],
        )

    def test_detail_txt_parser_keeps_crisfield_packham_iteration_data(self) -> None:
        detail = read_detail_txt(ORIGINAL / "zlamal2" / "zlamal2_1.txt")
        self.assertEqual(detail.d_code, 2)
        self.assertAlmostEqual(detail.d_sigma, 2000.0)
        self.assertEqual(len(detail.d_crush_vectors), 3)
        self.assertEqual([len(vector) for vector in detail.d_crush_vectors], [41, 41, 41])

    def test_scipy_linprog_reproduces_crisfield_packham_reference_solution(self) -> None:
        root = ORIGINAL / "zlamal2"
        detail = read_detail_txt(root / "zlamal2_1.txt")
        ab = read_ab_dump(root / "zlamal2_1.AB", block_count=detail.block_count)
        simplex = read_simplex_dump(root / "zlamal2_1.sim")

        model = build_linprog_model(detail, ab, simplex)
        result = solve_linprog_model(model)

        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.load_factor, detail.final_result_summary.load_factor, delta=5e-5)
        active = [index + 1 for index, value in enumerate(result.mechanism) if value > 1e-5]
        self.assertEqual(active, [1, 16, 51, 82])

    def test_builder_reproduces_reference_detail_tables(self) -> None:
        root = ORIGINAL / "zlamal0"
        prepared = prepare_melb_input(read_melb_input(root / "zlamal0_1.in"))
        detail = read_detail_txt(root / "zlamal0_1.txt")

        self.assertLess(max(abs((prepared.intrados_extrados - detail.intrados_extrados).ravel())), 1e-5)
        self.assertLess(max(abs((prepared.masonry_weights - detail.masonry_weights).ravel())), 1e-5)
        self.assertLess(max(abs((prepared.fill_weights - detail.fill_weights).ravel())), 3e-5)
        self.assertLess(max(abs((prepared.external_loads - detail.external_loads).ravel())), 1e-5)
        self.assertLess(max(abs((prepared.local_coordinates - detail.local_coordinates).ravel())), 1e-5)
        self.assertLess(max(abs((prepared.transformed_masonry - detail.transformed_masonry).ravel())), 1e-5)
        self.assertLess(max(abs((prepared.transformed_fill - detail.transformed_fill).ravel())), 1e-5)
        self.assertLess(max(abs((prepared.transformed_external - detail.transformed_external).ravel())), 1e-5)

    def test_builder_reproduces_reference_ab_and_simplex_dump(self) -> None:
        root = ORIGINAL / "zlamal0"
        prepared = prepare_melb_input(read_melb_input(root / "zlamal0_1.in"))
        ab = read_ab_dump(root / "zlamal0_1.AB", block_count=prepared.input.block_count)
        simplex = read_simplex_dump(root / "zlamal0_1.sim")
        generated_simplex = read_simplex_bytes(prepared.simplex_bytes)

        self.assertLess(max(abs((prepared.ab.matrix - ab.matrix).ravel())), 2e-6)
        self.assertEqual(generated_simplex.first_header, simplex.first_header)
        self.assertEqual(generated_simplex.second_header, simplex.second_header)
        self.assertEqual(generated_simplex.third_header, simplex.third_header)
        self.assertEqual(generated_simplex.trailing_ints, simplex.trailing_ints)
        self.assertLess(max(abs(generated_simplex.values - simplex.values)), 5e-6)

    def test_generated_input_ab_simplex_can_be_solved_with_linprog(self) -> None:
        root = ORIGINAL / "zlamal0"
        detail = read_detail_txt(root / "zlamal0_1.txt")
        prepared = prepare_melb_input(read_melb_input(root / "zlamal0_1.in"))
        simplex = read_simplex_bytes(prepared.simplex_bytes)

        model = build_linprog_model(detail, prepared.ab, simplex)
        result = solve_linprog_model(model)

        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.load_factor, detail.result.load_factor, delta=4e-5)

    def test_generated_livesley_iterations_match_reference(self) -> None:
        root = ORIGINAL / "zlamal1"
        detail = read_detail_txt(root / "zlamal1_1.txt")
        result = solve_melb_iterations(read_melb_input(root / "zlamal1_1.in"))

        self.assertEqual(len(result.steps), len(detail.result_summaries))
        self.assertAlmostEqual(result.final.load_factor, detail.final_result_summary.load_factor, delta=5e-5)

    def test_generated_crisfield_packham_iterations_match_reference(self) -> None:
        root = ORIGINAL / "zlamal2"
        detail = read_detail_txt(root / "zlamal2_1.txt")
        result = solve_melb_iterations(read_melb_input(root / "zlamal2_1.in"))

        self.assertEqual(len(result.steps), len(detail.result_summaries))
        self.assertAlmostEqual(result.final.load_factor, detail.final_result_summary.load_factor, delta=6e-5)

    def test_generated_interaction_diagram_iterations_match_reference(self) -> None:
        root = ORIGINAL / "zlamal3"
        detail = read_detail_txt(root / "zlamal3_1.txt")
        result = solve_melb_iterations(read_melb_input(root / "zlamal3_1.in"))

        self.assertEqual(len(result.steps), len(detail.result_summaries))
        self.assertAlmostEqual(result.final.load_factor, detail.final_result_summary.load_factor, delta=7e-5)

    def test_generated_lateral_soil_pressure_recalculation_matches_reference(self) -> None:
        detail = read_detail_txt(MELBOURNE / "test.txt")
        result = solve_melb_iterations(read_melb_input(MELBOURNE / "TEST.IN"))
        simplex = read_simplex_dump(MELBOURNE / "test.sim")
        generated_simplex = read_simplex_bytes(result.final.prepared.simplex_bytes)

        self.assertEqual(len(result.steps), 2)
        self.assertAlmostEqual(result.steps[0].load_factor, detail.result_summaries[0].load_factor, delta=2e-3)
        self.assertAlmostEqual(result.final.load_factor, detail.final_result_summary.load_factor, delta=1e-3)
        self.assertLess(max(abs(generated_simplex.values - simplex.values)), 3e-5)

    def test_q_code_1_uniform_load_spreading_is_supported(self) -> None:
        data = replace(read_melb_input(MELBOURNE / "TEST.IN"), q_code=1, k_fill=(0.0, 0.6, 0.4, 2.4, 0.0))
        prepared = prepare_melb_input(data)
        result = solve_melb_iterations(data)

        self.assertAlmostEqual(sum(prepared.external_loads[:, 2]), sum(load.force for load in data.point_loads))
        self.assertGreater(sum(abs(prepared.external_loads[:, 2]) > 1e-12), 1)
        self.assertTrue(result.final.load_factor > 0.0)

    def test_q_code_2_boussinesq_load_spreading_is_supported(self) -> None:
        data = replace(read_melb_input(MELBOURNE / "TEST.IN"), q_code=2, k_fill=(0.0, 0.6, 0.4, 2.4, 0.0))
        prepared = prepare_melb_input(data)
        result = solve_melb_iterations(data)

        self.assertGreater(sum(prepared.external_loads[:, 2]), 0.0)
        self.assertLessEqual(sum(prepared.external_loads[:, 2]), sum(load.force for load in data.point_loads))
        self.assertGreater(sum(abs(prepared.external_loads[:, 2]) > 1e-12), 1)
        self.assertTrue(result.final.load_factor > 0.0)

    def test_python_txt_and_out_outputs_are_written_and_parseable(self) -> None:
        temp_root = Path.cwd() / "tmp_test_outputs"
        temp_root.mkdir(exist_ok=True)
        txt_path = temp_root / "zlamal0_1_py.txt"
        out_path = temp_root / "zlamal0_1_py.out"
        result = write_melb_outputs(ORIGINAL / "zlamal0" / "zlamal0_1.in", txt_path, out_path)
        parsed = read_detail_txt(txt_path)
        txt_text = txt_path.read_text(encoding="utf-8")
        out_text = out_path.read_text(encoding="utf-8")

        self.assertAlmostEqual(parsed.final_result_summary.load_factor, result.final.load_factor, delta=1e-6)
        self.assertEqual(parsed.block_count, 40)
        self.assertIn("Transformovane zatizeni nadnasypem:", txt_text)
        self.assertIn("lambda =", out_text)

    def test_python_input_format_round_trips(self) -> None:
        data = read_melb_input(ORIGINAL / "zlamal0" / "zlamal0_1.in")
        temp_root = Path.cwd() / "tmp_test_outputs"
        temp_root.mkdir(exist_ok=True)
        input_path = temp_root / "zlamal0_1_roundtrip.in"
        input_path.write_text(format_melb_input(data, title="roundtrip"), encoding="utf-8")
        parsed = read_melb_input(input_path)

        self.assertEqual(parsed.span, data.span)
        self.assertEqual(parsed.rise, data.rise)
        self.assertEqual(parsed.geom_code, data.geom_code)
        self.assertEqual(parsed.block_count, data.block_count)
        self.assertEqual(parsed.point_loads, data.point_loads)
        for actual, expected in zip(parsed.k_fill, data.k_fill):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(parsed.d_code, data.d_code)

    def test_unbounded_solver_error_has_readable_message(self) -> None:
        data = read_melb_input(ORIGINAL / "zlamal0" / "zlamal0_1.in")
        result = LinprogResult(
            load_factor=float("nan"),
            variables=[],
            mechanism=[],
            success=False,
            status=3,
            message="The problem is unbounded.",
        )
        message = str(MelbSolveError(result, data))

        self.assertIn("linearni program je neomezeny", message)
        self.assertIn("zamkl", message)
        self.assertIn("Stav solveru: 3", message)


if __name__ == "__main__":
    unittest.main()

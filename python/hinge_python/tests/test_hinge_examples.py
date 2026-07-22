from __future__ import annotations

import unittest
from pathlib import Path

from hinge import compute_diagram, parse_input, plot_diagram, render_output


ORIGINAL = Path(r"D:\Documents\2026\MASARCH2026\hinge")


class HingeExamplesTest(unittest.TestCase):
    def assert_matches_example(self, stem: str) -> None:
        method, n, values = parse_input(ORIGINAL / f"{stem}.txt")
        rendered = render_output(compute_diagram(method, n, values))
        expected = (ORIGINAL / f"{stem}.out").read_text(encoding="cp1250")
        self.assertEqual(_numeric_lines(rendered), _numeric_lines(expected))

    def test_method1(self) -> None:
        self.assert_matches_example("pokus1")

    def test_method2(self) -> None:
        self.assert_matches_example("pokus2")

    def test_method3(self) -> None:
        self.assert_matches_example("pokus3")

    def test_method4(self) -> None:
        self.assert_matches_example("pokus4")

    def test_plot_output(self) -> None:
        method, n, values = parse_input(ORIGINAL / "pokus2.txt")
        diagram = compute_diagram(method, n, values)
        output_path = Path(__file__).with_name("_tmp_diagram.png")
        try:
            plot_diagram(diagram, output_path)
            self.assertGreater(output_path.stat().st_size, 1000)
        finally:
            output_path.unlink(missing_ok=True)


def _numeric_lines(text: str) -> list[str]:
    return [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("Interakcni")
    ]


if __name__ == "__main__":
    unittest.main()

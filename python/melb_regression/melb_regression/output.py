from __future__ import annotations

from pathlib import Path

import numpy as np

from .builder import PI, IterationResult, IterationStep, MelbInput, read_melb_input, solve_melb_iterations


def write_melb_outputs(
    input_path: str | Path,
    txt_path: str | Path,
    out_path: str | Path | None = None,
) -> IterationResult:
    data = read_melb_input(input_path)
    return write_melb_outputs_for_data(data, txt_path, out_path)


def write_melb_outputs_for_data(
    data: MelbInput,
    txt_path: str | Path,
    out_path: str | Path | None = None,
) -> IterationResult:
    result = solve_melb_iterations(data)
    Path(txt_path).write_text(format_detail_output(data, result), encoding="utf-8")
    if out_path is not None:
        Path(out_path).write_text(format_summary_output(data, result), encoding="utf-8")
    return result


def format_detail_output(data: MelbInput, result: IterationResult) -> str:
    prepared = result.steps[0].prepared
    lines = [
        f"Vstupni soubor: {data.path.name}",
        "*** Python MELB output ***",
        "",
    ]
    lines.extend(_input_summary(data))
    lines.append("*****************************")
    lines.extend(_table("Ortoganalni souradnice intrados a extrados:", "X_int\tY_int\tX_ext\tY_ext", prepared.intrados_extrados))
    lines.extend(_table("Vlastni tiha klenby - jednotlive bloky:", "X_G\tY_G\tG", prepared.masonry_weights))
    lines.extend(_table("Tiha nadnasypu pusobici na bloky:", "F_fill\tdY_ex\tX_fill\tY_fill", prepared.fill_weights))
    lines.extend(_table("Vnejsi zatizeni pusobici na bloky:", "X_q\tY_q\tQ", prepared.external_loads))
    lines.extend(_table("Ortogonalni lokalni souradnice jednotlivych bloku:", "a\talfa\tb\tbeta", prepared.local_coordinates))
    lines.extend(_table("Transformovane zatizeni vlastni tihou klenby:", "Px\tPy\tMp", prepared.transformed_masonry))
    lines.extend(_table("Transformovane zatizeni nadnasypem:", "Px\tPy\tMp", prepared.transformed_fill))
    lines.extend(_table("Transformovane zatizeni vnejsich sil:", "Qx\tQy\tMq", prepared.transformed_external))

    if len(result.steps) > 1 and data.k_fill[0] == 2.0:
        soil_step = result.steps[1]
        lines.append("")
        lines.append("*** Po prepocitani zemniho tlaku ***")
        lines.extend(_table("Nove transformovane zatizeni nadnasypem:", None, soil_step.prepared.transformed_fill))
        if data.k_fill[4] == 1.0:
            lines.extend(_table("Nove transformovane zatizeni vnejsich sil:", None, soil_step.prepared.transformed_external))

    lines.append("")
    lines.append("*** vysledky vypoctu ***")
    for position, step in enumerate(result.steps):
        if position > 0:
            delta = result.steps[position - 1].load_factor - step.load_factor
            lines.append("")
            lines.append(f" * Iterace c. {step.index} * Delta = {_fmt(delta)} *")
        lines.extend(_format_step(data, step))
        if step.d_crush is not None:
            title = " Vektor e_min:" if data.d_code == 4 else " Vektor d_crush:"
            lines.append(title)
            lines.append(_format_vector(step.d_crush))
    return "\n".join(lines) + "\n"


def format_summary_output(data: MelbInput, result: IterationResult) -> str:
    lines = [
        f"Vstupni soubor: {data.path.name}",
        "*** vysledky vypoctu ***",
    ]
    if len(result.steps) > 1:
        lines.append(f"pocet kroku = {len(result.steps)}")
    lines.extend(_format_step(data, result.final))
    return "\n".join(lines) + "\n"


def _input_summary(data: MelbInput) -> list[str]:
    lines = [
        _fmt(data.span),
        _fmt(data.rise),
        str(data.geom_code),
        _fmt(data.thickness),
        _fmt(data.masonry_unit_weight),
        _fmt(data.sliding_coefficient),
        str(data.block_count),
        str(len(data.point_loads)),
    ]
    for load in data.point_loads:
        lines.append(f"{_fmt(load.x)} {_fmt(load.force)} {_fmt(load.width)}")
    lines.extend(
        [
            _fmt(data.fill_height),
            _fmt(data.fill_unit_weight),
            f"{data.q_code} {_fmt(data.fill_spread_angle * 180.0 / PI)}",
            " ".join(_fmt(value) for value in data.k_fill),
            f"{data.d_code} {_fmt(data.d_sigma)} {data.interaction_file}",
            "",
        ]
    )
    return lines


def _format_step(data: MelbInput, step: IterationStep) -> list[str]:
    lines = [
        " icase = 0",
        "         0 -> O.K.,",
        "        -1 -> nelze splnit omezujici podminky,",
        "        +1 -> cilova funkce je na polyedru neomezena.",
        f" lambda = {_fmt(step.load_factor)}",
        f" pocet bloku N = {data.block_count}",
        " Vektor lokalnich deformaci:",
    ]
    lines.extend(_format_mechanism(step.mechanism, data.block_count))
    lines.append(" Vektor indexu spary mezi bloky:")
    lines.append(_format_int_vector(range(data.block_count + 1)))
    lines.append(" Vektor normalovych sil ve sparach (+ znaci tlak):")
    lines.append(_format_vector(step.normal_forces))
    lines.append(" Vektor vzdalenosti N od hornoho povrchu klenby:")
    lines.append(_format_vector(step.normal_distances))
    if data.sliding_coefficient > 0.0:
        lines.append(" Vektor posouvajicich sil ve sparach:")
        lines.append(_format_vector(step.shear_forces))
    return lines


def _format_mechanism(values: np.ndarray, block_count: int) -> list[str]:
    lines = []
    threshold = 1e-8
    for one_based in range(1, len(values) + 1, 2):
        first = values[one_based - 1]
        second = values[one_based] if one_based < len(values) else 0.0
        if one_based < 2 * block_count + 2:
            joint = one_based // 2
            if abs(first) > threshold:
                lines.append(f" {one_based:3d}: fi {joint:02d} int = {_fmt(first)}")
            if abs(second) > threshold:
                lines.append(f" {one_based + 1:3d}: fi {joint:02d} ext = {_fmt(second)}")
        else:
            joint = (one_based - 2 * block_count - 2) // 2
            if abs(first) > threshold:
                lines.append(f" {one_based:3d}:  y {joint:02d} (+) = {_fmt(first)}")
            if abs(second) > threshold:
                lines.append(f" {one_based + 1:3d}:  y {joint:02d} (-) = {_fmt(second)}")
    return lines


def _table(title: str, header: str | None, values: np.ndarray) -> list[str]:
    lines = ["", title]
    if header is not None:
        lines.append(header)
    lines.extend("\t".join(_fmt(value) for value in row) for row in values)
    return lines


def _format_vector(values) -> str:
    return "\t".join(_fmt(value) for value in values)


def _format_int_vector(values) -> str:
    return "\t\t".join(str(value) for value in values)


def _fmt(value: float) -> str:
    return f"{float(value):.6f}"

from __future__ import annotations

from dataclasses import dataclass
from math import fabs
from pathlib import Path


NPINS = 4
TOLERANCE = 1.0001
RAND_MAX = 32767


@dataclass(frozen=True)
class Force:
    x: float
    value: float


@dataclass(frozen=True)
class ArchInput:
    x: tuple[float, ...]
    y: tuple[float, ...]
    nd: tuple[float, ...]
    dead_loads: tuple[Force, ...]
    live_loads: tuple[Force, ...]
    seed: int
    mode: int
    generated_count: int


@dataclass(frozen=True)
class GeneratedRow:
    index: int
    generated_pins: tuple[int, ...]
    generated_ids: tuple[int, ...]
    ok: bool
    result_pins: tuple[int, ...] = ()
    result_ids: tuple[int, ...] = ()
    d: float = 0.0
    alfa: float = 0.0
    h: float = 0.0
    v: float = 0.0
    eps_h: float = 0.0


@dataclass(frozen=True)
class InternalForce:
    point: int
    h: float
    v: float
    e: float
    e_div_legacy: float
    moment: float


@dataclass(frozen=True)
class AnalysisResult:
    data: ArchInput
    ok_count: int
    gauss_errors: int
    oscil_errors: int
    result_pins: tuple[int, ...]
    result_ids: tuple[int, ...]
    d: float
    alfa: float
    h: float
    v: float
    eps_h: float
    internal_forces: tuple[InternalForce, ...]
    generated_rows: tuple[GeneratedRow, ...]


@dataclass(frozen=True)
class LoadTables:
    dead_f: tuple[tuple[float, ...], ...]
    dead_m: tuple[tuple[float, ...], ...]
    live_f: tuple[tuple[float, ...], ...]
    live_m: tuple[tuple[float, ...], ...]


class CRand:
    """MSVCRT/MinGW-compatible rand() used by the original Dev-C++ program."""

    def __init__(self, seed: int) -> None:
        self.seed = seed & 0xFFFFFFFF

    def rand(self) -> int:
        self.seed = (214013 * self.seed + 2531011) & 0xFFFFFFFF
        return (self.seed >> 16) & 0x7FFF


def parse_input(path: str | Path) -> ArchInput:
    tokens = Path(path).read_text(encoding="cp1250").split()
    pos = 0

    def next_int() -> int:
        nonlocal pos
        value = int(float(tokens[pos]))
        pos += 1
        return value

    def next_float() -> float:
        nonlocal pos
        value = float(tokens[pos])
        pos += 1
        return value

    npoints = next_int()
    x: list[float] = []
    y: list[float] = []
    nd: list[float] = []
    for _ in range(npoints):
        x.append(next_float())
        y.append(next_float())
        nd.append(next_float())

    nw = next_int()
    dead_loads = tuple(Force(next_float(), next_float()) for _ in range(nw))

    np = next_int()
    live_loads = tuple(Force(next_float(), next_float()) for _ in range(np))

    seed = next_int()
    mode = next_int()
    generated_count = next_int()
    if mode not in {1, 2}:
        raise ValueError(f"MODE must be 1 or 2, got {mode}.")
    return ArchInput(
        x=tuple(x),
        y=tuple(y),
        nd=tuple(nd),
        dead_loads=dead_loads,
        live_loads=live_loads,
        seed=seed,
        mode=mode,
        generated_count=generated_count,
    )


def analyze(data: ArchInput, list_generated: bool = False) -> AnalysisResult:
    rng = CRand(data.seed)
    loads = _build_load_tables(data)
    ok_count = 0
    gauss_errors = 0
    oscil_errors = 0
    result_pins = (0, 0, 0, 0)
    result_ids = (0, 0, 0, 0)
    result_d = 0.0
    result_alfa = 0.0
    result_h = 0.0
    result_v = 0.0
    result_eps_h = 0.0
    rows: list[GeneratedRow] = []

    for igen in range(data.generated_count):
        generated_pins, generated_ids = _generate_initial(data, rng)
        pins = list(generated_pins)
        ids = list(generated_ids)
        h1_pins = [0] * NPINS
        h2_pins = [0] * NPINS
        h3_pins = [0] * NPINS
        h1_ids = [0] * NPINS
        h2_ids = [0] * NPINS
        h3_ids = [0] * NPINS

        d = 1.0
        alfa = 1.0
        h = 0.0
        v = 0.0
        eps_h = 0.0
        gauss_test = False
        oscil_test = False
        iterate = True

        while iterate:
            try:
                if data.mode == 1:
                    a, b = _mode1_system(data, loads, pins, ids)
                    c = _gauss_elim(a, b)
                    d = c[2]
                    if c[1] == 0:
                        gauss_test = True
                        gauss_errors += 1
                        break
                    h = 1.0 / c[1]
                    v = c[0] * h
                    alfa = 1.0
                else:
                    a, b = _mode2_system(data, loads, pins, ids)
                    c = _gauss_elim(a, b)
                    alfa = c[2]
                    h = c[1]
                    v = c[0]
                    d = 1.0
            except LinearDependencyError:
                gauss_test = True
                gauss_errors += 1
                break

            v = v + alfa * loads.live_f[pins[-1]][len(data.x) - 1]
            v = v + loads.dead_f[pins[-1]][len(data.x) - 1]
            if h == 0:
                gauss_test = True
                gauss_errors += 1
                break
            eps_h = (
                alfa * loads.live_m[pins[-1]][len(data.x) - 1]
                + loads.dead_m[pins[-1]][len(data.x) - 1]
                - v * (data.x[-1] - data.x[pins[-1]])
            ) / h
            eps_h += data.y[pins[-1]] - data.y[-1] + ids[-1] * data.nd[pins[-1]] * d

            e = _pressure_line_e(data, loads, d, alfa, h, v, eps_h)
            iterate = any(
                fabs(e[i]) > TOLERANCE * (data.nd[i] * d / 2.0)
                for i in range(len(data.x))
            )
            if d < 0 or alfa < 0:
                iterate = True

            h1_pins, h2_pins, h3_pins = h2_pins, h3_pins, pins.copy()
            h1_ids, h2_ids, h3_ids = h2_ids, h3_ids, ids.copy()

            e_div = [e[i] / (data.nd[i] * d / 2.0) for i in range(len(e))]
            pins, ids = _finder(e_div, NPINS)
            if d < 0 or alfa < 0:
                ids = [1 if item == 0 else 0 for item in ids]

            oscil_test = pins == h2_pins and ids == h2_ids
            if not oscil_test:
                oscil_test = pins == h1_pins and ids == h1_ids
            if oscil_test:
                iterate = False
                oscil_errors += 1

        ok = not gauss_test and not oscil_test
        if list_generated:
            rows.append(
                GeneratedRow(
                    index=igen,
                    generated_pins=generated_pins,
                    generated_ids=generated_ids,
                    ok=ok,
                    result_pins=tuple(pins) if ok else (),
                    result_ids=tuple(ids) if ok else (),
                    d=d,
                    alfa=alfa,
                    h=h,
                    v=v,
                    eps_h=eps_h,
                )
            )

        if ok:
            if ok_count == 0:
                ok_count = 1
                result_pins = tuple(pins)
                result_ids = tuple(ids)
                result_d, result_alfa, result_h, result_v, result_eps_h = (
                    d,
                    alfa,
                    h,
                    v,
                    eps_h,
                )
            else:
                better = (
                    data.mode == 1
                    and result_d > d
                    or data.mode == 2
                    and result_alfa < alfa
                )
                if better:
                    ok_count = 1
                    result_pins = tuple(pins)
                    result_ids = tuple(ids)
                    result_d, result_alfa, result_h, result_v, result_eps_h = (
                        d,
                        alfa,
                        h,
                        v,
                        eps_h,
                    )
                if (
                    data.mode == 1
                    and result_d == d
                    or data.mode == 2
                    and result_alfa == alfa
                ):
                    ok_count += 1

    internal = _internal_forces(
        data, loads, result_d, result_alfa, result_h, result_v, result_eps_h
    ) if result_h != 0 else []
    return AnalysisResult(
        data=data,
        ok_count=ok_count,
        gauss_errors=gauss_errors,
        oscil_errors=oscil_errors,
        result_pins=result_pins,
        result_ids=result_ids,
        d=result_d,
        alfa=result_alfa,
        h=result_h,
        v=result_v,
        eps_h=result_eps_h,
        internal_forces=tuple(internal),
        generated_rows=tuple(rows),
    )


def render_output(
    result: AnalysisResult,
    input_name: str = "input.txt",
    include_generated: bool = False,
) -> str:
    data = result.data
    lines: list[str] = [f" Input file: {input_name}", " Start of computation: Python port", ""]
    if include_generated:
        lines.append(
            "# No. | Generovane_body_poruseni Tvar_poruseni | Result | "
            "Vysledne_body_poruseni Vysledny_tvar_poruseni | "
            "D[m] alfa[-] H[kN] V[kN] EpsH[m]"
        )
        for row in result.generated_rows:
            prefix = _format_row_ints(row.generated_pins + row.generated_ids)
            if row.ok:
                suffix = _format_row_ints(row.result_pins + row.result_ids)
                lines.append(
                    f"# {row.index} |{prefix} | OK |{suffix} | "
                    f"{row.d:.6f} {row.alfa:.6f} {row.h:.6f} {row.v:.6f} {row.eps_h:.6f}"
                )
            else:
                lines.append(f"# {row.index} |{prefix} | ERROR")
    lines.extend(
        [
            "",
            "",
            " ***  RESULTS  ***",
            "",
            " Cas vypoctu:   0.00 sec",
            f" Vypocet probehl v MODE {data.mode}",
            f" Parametr generatoru: {data.seed}",
            "",
            f" Pocet generovanych tvaru poruseni: {data.generated_count}",
            f" - pocet vysledku OK:        {result.ok_count:3d}",
            f" - pocet ERROR_GaussElim:    {result.gauss_errors:3d}",
            f" - pocet ERROR_Oscilace:     {result.oscil_errors:3d}",
            f" - pocet ostatnich vysledku: {data.generated_count - result.ok_count - result.gauss_errors - result.oscil_errors:3d}",
            "",
            " | Vysledne_body_poruseni | Vysledny_tvar_poruseni |",
            f" |{_format_row_ints(result.result_pins)} |{_format_row_ints(result.result_ids)} |",
            "",
            "D[m] alfa[-] H[kN] V[kN] EpsH[m]",
            f" {result.d:.6f} {result.alfa:.6f} {result.h:.6f} {result.v:.6f} {result.eps_h:.6f}",
            "",
            "",
            " Internal forces:",
            " Point H[kN] V[kN] e[m] e/D[-] M[kNm]",
        ]
    )
    for item in result.internal_forces:
        lines.append(
            f" {item.point} {item.h:.6f} {item.v:.6f} {item.e:.6f} "
            f"{item.e_div_legacy:.6f} {item.moment:.6f}"
        )
    lines.extend(["", "", " AutoCAD commands:", ""])
    e_values = [item.e for item in result.internal_forces]
    if not e_values:
        return "\n".join(lines) + "\n"
    for i in range(len(data.x) - 1):
        lines.append(f"line {data.x[i]:.6f},{data.y[i]:.6f} {data.x[i+1]:.6f},{data.y[i+1]:.6f} ")
        lines.append("")
        lines.append(
            f"line {data.x[i]:.6f},{data.y[i] + data.nd[i] * result.d:.6f} "
            f"{data.x[i+1]:.6f},{data.y[i+1] + data.nd[i+1] * result.d:.6f} "
        )
        lines.append("")
        lines.append(
            f"line {data.x[i]:.6f},{data.y[i] + data.nd[i] * result.d / 2.0 + e_values[i]:.6f} "
            f"{data.x[i+1]:.6f},{data.y[i+1] + data.nd[i+1] * result.d / 2.0 + e_values[i+1]:.6f} "
        )
        lines.append("")
    return "\n".join(lines) + "\n"


def _format_row_ints(values: tuple[int, ...]) -> str:
    return "".join(f" {value}" for value in values)


class LinearDependencyError(Exception):
    pass


def _generate_initial(data: ArchInput, rng: CRand) -> tuple[tuple[int, ...], tuple[int, ...]]:
    pins = [int(rng.rand() * len(data.x) / RAND_MAX)]
    while len(pins) < NPINS:
        candidate = int(rng.rand() * len(data.x) / RAND_MAX)
        if candidate not in pins:
            pins.append(candidate)
    pins.sort()
    ids = [rng.rand() % 2 for _ in range(NPINS)]
    return tuple(pins), tuple(ids)


def _sum_f(loads: tuple[Force, ...], x_left: float, x_right: float) -> float:
    return sum(load.value for load in loads if x_left <= load.x < x_right)


def _sum_m(loads: tuple[Force, ...], x_left: float, x_right: float) -> float:
    return sum(load.value * (load.x - x_left) for load in loads if x_left <= load.x < x_right)


def _build_load_tables(data: ArchInput) -> LoadTables:
    dead_f, dead_m = _build_single_load_table(data.x, data.dead_loads)
    live_f, live_m = _build_single_load_table(data.x, data.live_loads)
    return LoadTables(
        dead_f=dead_f,
        dead_m=dead_m,
        live_f=live_f,
        live_m=live_m,
    )


def _build_single_load_table(
    x: tuple[float, ...],
    loads: tuple[Force, ...],
) -> tuple[tuple[tuple[float, ...], ...], tuple[tuple[float, ...], ...]]:
    n = len(x)
    force_rows: list[tuple[float, ...]] = []
    moment_rows: list[tuple[float, ...]] = []
    for i in range(n):
        force_row: list[float] = []
        moment_row: list[float] = []
        for j in range(n):
            if j <= i:
                force_row.append(0.0)
                moment_row.append(0.0)
            else:
                force = _sum_f(loads, x[i], x[j])
                moment = _sum_m(loads, x[i], x[j])
                force_row.append(force)
                moment_row.append(moment)
        force_rows.append(tuple(force_row))
        moment_rows.append(tuple(moment_row))
    return tuple(force_rows), tuple(moment_rows)


def _mode1_system(data: ArchInput, loads: LoadTables, pins: list[int], ids: list[int]) -> tuple[list[list[float]], list[float]]:
    a = [[0.0 for _ in range(NPINS - 1)] for _ in range(NPINS - 1)]
    b = [0.0 for _ in range(NPINS - 1)]
    for i in range(NPINS - 1):
        a[i][0] = data.x[pins[-1]] - data.x[pins[i]]
        a[i][1] -= loads.live_m[pins[i]][pins[-1]]
        a[i][1] -= loads.dead_m[pins[i]][pins[-1]]
        a[i][2] = ids[-1] * data.nd[pins[-1]] - ids[i] * data.nd[pins[i]]
        b[i] = data.y[pins[i]] - data.y[pins[-1]]
    return a, b


def _mode2_system(data: ArchInput, loads: LoadTables, pins: list[int], ids: list[int]) -> tuple[list[list[float]], list[float]]:
    a = [[0.0 for _ in range(NPINS - 1)] for _ in range(NPINS - 1)]
    b = [0.0 for _ in range(NPINS - 1)]
    for i in range(NPINS - 1):
        a[i][0] = data.x[pins[-1]] - data.x[pins[i]]
        a[i][1] = (
            ids[-1] * data.nd[pins[-1]]
            - ids[i] * data.nd[pins[i]]
            + data.y[pins[-1]]
            - data.y[pins[i]]
        )
        a[i][2] = -loads.live_m[pins[i]][pins[-1]]
        b[i] = loads.dead_m[pins[i]][pins[-1]]
    return a, b


def _gauss_elim(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    a = [row[:] for row in a]
    b = b[:]
    c = [0.0] * n
    for i in range(n - 1):
        if a[i][i] == 0:
            if i == 0 and all(a[0][k] == 0 for k in range(i + 1, n)):
                raise LinearDependencyError()
            swap = 0
            for k in range(i + 1, n):
                if a[k][i] != 0:
                    swap = k
            if swap == 0:
                raise LinearDependencyError()
            a[i], a[swap] = a[swap], a[i]
            b[i], b[swap] = b[swap], b[i]
        for j in range(i + 1, n):
            pom = -(a[j][i] / a[i][i])
            for k in range(i, n):
                a[j][k] = a[j][k] + pom * a[i][k]
            b[j] = b[j] + pom * b[i]
        if all(a[i + 1][k] == 0 for k in range(i + 1, n)):
            raise LinearDependencyError()
    for i in range(n):
        row = n - 1 - i
        for j in range(i):
            b[row] = b[row] - a[n - 1 - i][n - 1 - j] * c[n - 1 - j]
        c[row] = b[row] / a[n - 1 - i][n - 1 - i]
    return c


def _pressure_line_e(
    data: ArchInput,
    loads: LoadTables,
    d: float,
    alfa: float,
    h: float,
    v: float,
    eps_h: float,
) -> list[float]:
    e: list[float] = []
    for i in range(len(data.x)):
        value = (
            -alfa * loads.live_m[i][len(data.x) - 1]
            - loads.dead_m[i][len(data.x) - 1]
            + v * (data.x[-1] - data.x[i])
        ) / h
        value -= data.y[i] - data.y[-1] - eps_h
        value -= data.nd[i] * d / 2.0
        e.append(value)
    return e


def _finder(e: list[float], m: int) -> tuple[list[int], list[int]]:
    pins = [0] * m
    counter = 0
    for i in range(len(e)):
        k1 = fabs(e[i]) if i == 0 else fabs(e[i]) - fabs(e[i - 1])
        k2 = -fabs(e[i]) if i == len(e) - 1 else fabs(e[i + 1]) - fabs(e[i])
        if k1 > 0 and k1 * k2 <= 0:
            if counter <= m - 1:
                pins[counter] = i
                counter += 1
            else:
                pins.sort(key=lambda idx: fabs(e[idx]), reverse=True)
                if fabs(e[i]) >= fabs(e[pins[0]]):
                    pins[3] = pins[2]
                    pins[2] = pins[1]
                    pins[1] = pins[0]
                    pins[0] = i
                if fabs(e[pins[0]]) > fabs(e[i]) >= fabs(e[pins[1]]):
                    pins[3] = pins[2]
                    pins[2] = pins[1]
                    pins[1] = i
                if fabs(e[pins[1]]) > fabs(e[i]) >= fabs(e[pins[2]]):
                    pins[3] = pins[2]
                    pins[2] = i
                if fabs(e[pins[2]]) > fabs(e[i]) >= fabs(e[pins[3]]):
                    pins[3] = i
    while counter <= m - 1:
        max_value = 0.0
        candidate = 0
        for i, value in enumerate(e):
            if i not in pins[:counter] and fabs(value) >= max_value:
                max_value = fabs(value)
                candidate = i
        pins[counter] = candidate
        counter += 1
    pins.sort()
    ids = [0 if e[p] < 0 else 1 for p in pins]
    return pins, ids


def _internal_forces(
    data: ArchInput,
    loads: LoadTables,
    d: float,
    alfa: float,
    h: float,
    v: float,
    eps_h: float,
) -> list[InternalForce]:
    e = _pressure_line_e(data, loads, d, alfa, h, v, eps_h)
    items: list[InternalForce] = []
    for i, e_value in enumerate(e):
        vv = v - alfa * loads.live_f[i][len(data.x) - 1]
        vv -= loads.dead_f[i][len(data.x) - 1]
        items.append(
            InternalForce(
                point=i,
                h=h,
                v=vv,
                e=e_value,
                e_div_legacy=e_value / data.nd[i] * d,
                moment=h * e_value,
            )
        )
    return items

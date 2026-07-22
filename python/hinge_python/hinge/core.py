from __future__ import annotations

from dataclasses import dataclass
from math import fabs
from pathlib import Path


CHYBA = 0.1
KROK_D_EF = 0.000001
KROK_EPS_2 = 0.000001


@dataclass(frozen=True)
class Point:
    axial_force: float
    moment: float


@dataclass(frozen=True)
class Diagram:
    method: int
    points: tuple[Point, ...]

    @property
    def n(self) -> int:
        return len(self.points) - 1

    @property
    def max_axial_force(self) -> float:
        return self.points[-1].axial_force


def parse_input(path: str | Path) -> tuple[int, int, list[float]]:
    """Read the original HINGE input format.

    The first line is a free comment, then only numeric values follow.
    """
    lines = Path(path).read_text(encoding="cp1250").splitlines()
    tokens: list[str] = []
    for line in lines[1:]:
        tokens.extend(line.split())
    if len(tokens) < 2:
        raise ValueError("Input file does not contain METHOD and N.")
    method = int(tokens[0])
    n = int(tokens[1])
    values = [float(token) for token in tokens[2:]]
    if n <= 0:
        raise ValueError(f"N must be positive, got {n}.")
    if method not in {1, 2, 3, 4}:
        raise ValueError(f"METHOD must be one of 1, 2, 3, 4; got {method}.")
    return method, n, values


def compute_diagram(method: int, n: int, values: list[float]) -> Diagram:
    if method == 1:
        points = _method1(n, values)
    elif method == 2:
        points = _method2(n, values)
    elif method == 3:
        points = _method3(n, values)
    elif method == 4:
        points = _method4(n, values)
    else:
        raise ValueError(f"METHOD must be one of 1, 2, 3, 4; got {method}.")
    return Diagram(method=method, points=tuple(points))


def render_output(diagram: Diagram) -> str:
    lines = [
        f" Interakcni diagram - METHOD={diagram.method}",
        f" {diagram.n}",
        f" {diagram.max_axial_force:.6f}",
        "",
    ]
    lines.extend(
        f" {point.axial_force:.6f} {point.moment:.6f}"
        for point in diagram.points
    )
    return "\n".join(lines) + "\n"


def _require_count(method: int, values: list[float], count: int) -> None:
    if len(values) < count:
        raise ValueError(f"METHOD={method} requires {count} numeric values.")


def _method2(n: int, values: list[float]) -> list[Point]:
    _require_count(2, values, 3)
    b, h, sigma = values[:3]
    max_m = 0.125 * b * h * h * sigma
    max_p = b * h * sigma
    delta_p = max_p / n
    return [
        Point(p, _method2_m_for_p(p, max_p, max_m))
        for p in (delta_p * i for i in range(n + 1))
    ]


def _method2_m_for_p(p: float, max_p: float, max_m: float) -> float:
    if p > max_p or p < 0:
        return 0.0
    return 4 * max_m * (p / max_p - (p / max_p) ** 2)


def _method4(n: int, values: list[float]) -> list[Point]:
    _require_count(4, values, 3)
    b, h, sigma = values[:3]
    max_m = 0.09375 * b * h * h * sigma
    max_p = b * h * sigma
    delta_p = max_p / n
    return [
        Point(p, _method4_m_for_p(p, max_p, max_m))
        for p in (delta_p * i for i in range(n + 1))
    ]


def _method4_m_for_p(p: float, max_p: float, max_m: float) -> float:
    if p > max_p or p < 0:
        return 0.0
    if p > max_p / 2:
        return 16.0 / 9.0 * max_m * (1 - p / max_p)
    return 16.0 / 9.0 * max_m * (3 * p / max_p - 4 * (p / max_p) ** 2)


def _method1(n: int, values: list[float]) -> list[Point]:
    _require_count(1, values, 6)
    b, h, sigma_m, eps_m, lam = values[:5]
    k = int(values[5])
    max_p = b * h * sigma_m
    delta_p = max_p / n
    points = [Point(0.0, 0.0)]
    crack = 1
    d_ef0 = 0.0
    eps20 = 0.0

    for i in range(1, n):
        target = delta_p * i
        if crack == 1:
            eps1 = lam * eps_m
            if i == 1:
                d_ef0 = 2 * target / sigma_m / b
            p0 = _method1_p_crack(eps1, eps_m, sigma_m, b, d_ef0, h, k)
            while fabs(p0 - target) > CHYBA:
                d_ef1 = d_ef0 + KROK_D_EF
                p1 = _method1_p_crack(eps1, eps_m, sigma_m, b, d_ef1, h, k)
                d_ef0 = d_ef0 + (d_ef1 - d_ef0) / (p1 - p0) * (target - p0)
                p0 = _method1_p_crack(eps1, eps_m, sigma_m, b, d_ef0, h, k)
            moment = _method1_m_crack(eps1, eps_m, sigma_m, b, d_ef0, h, k)
            if d_ef0 > h:
                crack = -1

        if crack != 1:
            if crack == -1:
                eps20 = 0.0
                crack = 0
            eps1 = lam * eps_m - (lam - 1) * eps20
            p0 = _method1_p_uncrack(eps1, eps20, eps_m, sigma_m, b, h, k)
            while fabs(p0 - target) > CHYBA:
                eps21 = eps20 + KROK_EPS_2
                eps1 = lam * eps_m - (lam - 1) * eps20
                p1 = _method1_p_uncrack(eps1, eps21, eps_m, sigma_m, b, h, k)
                eps20 = eps20 + (eps21 - eps20) / (p1 - p0) * (target - p0)
                p0 = _method1_p_uncrack(eps1, eps20, eps_m, sigma_m, b, h, k)
            moment = _method1_m_uncrack(eps1, eps20, eps_m, sigma_m, b, h, k)

        points.append(Point(p0, moment))

    points.append(Point(max_p, 0.0))
    return points


def _method1_p_uncrack(
    eps1: float,
    eps2: float,
    eps_m: float,
    sigma_m: float,
    b: float,
    d: float,
    k: int,
) -> float:
    return (
        sigma_m
        * b
        * d
        * (
            k * (eps1 + eps2) / 2
            + (eps2 ** (k + 1) - eps1 ** (k + 1))
            / ((k + 1) * (eps1 - eps2) * eps_m ** (k - 1))
        )
        / ((k - 1) * eps_m)
    )


def _method1_m_uncrack(
    eps1: float,
    eps2: float,
    eps_m: float,
    sigma_m: float,
    b: float,
    d: float,
    k: int,
) -> float:
    return (
        sigma_m
        * b
        * d
        * d
        * (
            k * (eps1 - eps2) / 12
            - (eps1 ** (k + 1) + eps2 ** (k + 1))
            / (2 * (k + 1) * (eps1 - eps2) * eps_m ** (k - 1))
            + (eps1 ** (k + 2) - eps2 ** (k + 2))
            / ((k + 1) * (k + 2) * (eps1 - eps2) ** 2 * eps_m ** (k - 1))
        )
        / ((k - 1) * eps_m)
    )


def _method1_p_crack(
    eps1: float,
    eps_m: float,
    sigma_m: float,
    b: float,
    d_ef: float,
    d: float,
    k: int,
) -> float:
    return (
        sigma_m
        * b
        * eps1
        * d_ef
        * (k / 2 - (eps1 / eps_m) ** (k - 1) / (k + 1))
        / ((k - 1) * eps_m)
    )


def _method1_m_crack(
    eps1: float,
    eps_m: float,
    sigma_m: float,
    b: float,
    d_ef: float,
    d: float,
    k: int,
) -> float:
    return (
        sigma_m
        * b
        * eps1
        * d_ef
        * (
            k * (3 * d - 2 * d_ef) / 6
            - eps1 ** (k - 1)
            * (d - 2 * d_ef / (k + 2))
            / ((k + 1) * eps_m ** (k - 1))
        )
        / (2 * (k - 1) * eps_m)
    )


def _method3(n: int, values: list[float]) -> list[Point]:
    _require_count(3, values, 5)
    b, h, sig_m, eps_m, lam = values[:5]
    max_p = b * h * sig_m
    delta_p = max_p / n
    points = [Point(0.0, 0.0)]
    crack = 1
    d_ef0 = 0.0
    eps10 = 0.0

    for i in range(1, n):
        target = delta_p * i
        if crack == 1:
            if i == 1:
                d_ef0 = 2.0 * target / sig_m / b
            p0 = _bilin_p_crack(sig_m, d_ef0, lam, b)
            while fabs(p0 - target) > CHYBA:
                d_ef1 = d_ef0 + KROK_D_EF
                p1 = _bilin_p_crack(sig_m, d_ef1, lam, b)
                d_ef0 = d_ef0 + (d_ef1 - d_ef0) / (p1 - p0) * (target - p0)
                p0 = _bilin_p_crack(sig_m, d_ef0, lam, b)
            moment = _bilin_m_crack(sig_m, h, d_ef0, lam, b)
            if d_ef0 > h:
                crack = -1

        if crack != 1:
            if crack == -1:
                eps10 = 0.0
                crack = 0
            p0 = _bilin_p_uncrack(sig_m, eps_m, eps10, h, lam, b)
            while fabs(p0 - target) > CHYBA:
                eps11 = eps10 + KROK_EPS_2
                p1 = _bilin_p_uncrack(sig_m, eps_m, eps11, h, lam, b)
                eps10 = eps10 + (eps11 - eps10) / (p1 - p0) * (target - p0)
                p0 = _bilin_p_uncrack(sig_m, eps_m, eps10, h, lam, b)
            moment = _bilin_m_uncrack(sig_m, eps_m, eps10, h, lam, b)

        points.append(Point(p0, moment))

    points.append(Point(max_p, 0.0))
    return points


def _bilin_p_crack(sig_m: float, d_ef: float, lam: float, b: float) -> float:
    return sig_m * d_ef * b * (1.0 - 1.0 / (2.0 * lam))


def _bilin_m_crack(
    sig_m: float,
    h: float,
    d_ef: float,
    lam: float,
    b: float,
) -> float:
    return sig_m * b * (
        0.5 * (d_ef - d_ef / lam) * (h - d_ef + d_ef / lam)
        + 0.5 * d_ef / lam * (h / 2.0 - d_ef + 2.0 / 3.0 * d_ef / lam)
    )


def _bilin_p_uncrack(
    sig_m: float,
    eps_m: float,
    eps1: float,
    h: float,
    lam: float,
    b: float,
) -> float:
    return sig_m * b * (
        h
        - 0.5
        * h
        * (eps_m - eps1)
        / (lam * eps_m - eps1)
        * (1.0 - eps1 / eps_m)
    )


def _bilin_m_uncrack(
    sig_m: float,
    eps_m: float,
    eps1: float,
    h: float,
    lam: float,
    b: float,
) -> float:
    return (
        0.5
        * sig_m
        * b
        * (h * (eps_m - eps1) / (lam * eps_m - eps1))
        * (1 - eps1 / eps_m)
        * (h / 2 - 1.0 / 3 * (h * (eps_m - eps1) / (lam * eps_m - eps1)))
    )

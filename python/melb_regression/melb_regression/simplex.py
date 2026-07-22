from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct

import numpy as np


@dataclass(frozen=True)
class SimplexDump:
    path: Path
    first_header: int
    second_header: int
    third_header: int
    values: np.ndarray
    constraint_counts: tuple[int, ...] | None = None

    @property
    def raw_cell_count(self) -> int:
        return int(self.values.size)

    @property
    def as_rows_by_header(self) -> np.ndarray:
        rows = self.second_header + 1
        columns = self.first_header + 1
        count = rows * columns
        if count > self.values.size:
            raise ValueError("simplex dump is too small for header-shaped table")
        return self.values[:count].reshape((rows, columns))

    @property
    def as_constraints_by_header(self) -> np.ndarray:
        rows = self.first_header + 1
        columns = self.second_header + 1
        count = rows * columns
        if count > self.values.size:
            raise ValueError("simplex dump is too small for transposed header-shaped table")
        return self.values[:count].reshape((rows, columns))

    @property
    def trailing_values(self) -> np.ndarray:
        count = (self.second_header + 1) * (self.first_header + 1)
        return self.values[count:]

    @property
    def trailing_ints(self) -> tuple[int, ...]:
        if self.constraint_counts is not None:
            return self.constraint_counts
        count = (self.second_header + 1) * (self.first_header + 1)
        raw = self.path.read_bytes()[12 + 4 * count :]
        return struct.unpack("<" + "i" * (len(raw) // 4), raw)

    @property
    def nr_variable_count(self) -> int:
        return self.first_header

    @property
    def nr_constraint_counts(self) -> tuple[int, int, int]:
        return self.trailing_ints

    @property
    def nr_constraint_count(self) -> int:
        return sum(self.nr_constraint_counts)

    @property
    def nr_tableau(self) -> np.ndarray:
        return self.as_rows_by_header

    @property
    def objective_coefficients(self) -> np.ndarray:
        return self.nr_tableau[0, :-1]

    @property
    def equality_rows(self) -> np.ndarray:
        return self.nr_tableau[1 : 1 + self.nr_constraint_count, :-1]

    @property
    def equality_rhs(self) -> np.ndarray:
        return self.nr_tableau[1 : 1 + self.nr_constraint_count, -1]

    @property
    def auxiliary_objective_coefficients(self) -> np.ndarray:
        return self.nr_tableau[1 + self.nr_constraint_count, :-1]

    @property
    def streamed_blocks(self) -> tuple[np.ndarray, ...]:
        count = self.nr_variable_count
        blocks = []
        for index in range(self.second_header + 1):
            start = index * count
            end = start + count
            blocks.append(self.values[start:end])
        return tuple(blocks)


def read_simplex_dump(path: str | Path) -> SimplexDump:
    dump_path = Path(path)
    data = dump_path.read_bytes()
    return read_simplex_bytes(data, dump_path)


def read_simplex_bytes(data: bytes, path: str | Path = "<bytes>") -> SimplexDump:
    dump_path = Path(path)
    if len(data) < 12 or (len(data) - 12) % 4:
        raise ValueError(f"{dump_path} is not a MELB simplex dump")
    first, second, third = struct.unpack("<3i", data[:12])
    values = np.array(
        struct.unpack("<" + "f" * ((len(data) - 12) // 4), data[12:]),
        dtype=float,
    )
    count = (second + 1) * (first + 1)
    raw_trailing = data[12 + 4 * count :]
    trailing = struct.unpack("<" + "i" * (len(raw_trailing) // 4), raw_trailing)
    return SimplexDump(path=dump_path, first_header=first, second_header=second, third_header=third, values=values, constraint_counts=trailing)

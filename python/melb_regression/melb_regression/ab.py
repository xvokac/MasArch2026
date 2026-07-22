from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct

import numpy as np


@dataclass(frozen=True)
class ABDump:
    path: Path
    block_count: int
    matrix: np.ndarray

    @property
    def joint_count(self) -> int:
        return self.block_count + 1

    @property
    def expected_shape(self) -> tuple[int, int]:
        joints = self.joint_count
        return 4 * joints, 3 * joints

    @property
    def phi_rows(self) -> np.ndarray:
        return self.matrix[: 2 * self.joint_count]

    @property
    def sliding_rows(self) -> np.ndarray:
        return self.matrix[2 * self.joint_count :]

    def phi_row_pair(self, joint_index: int) -> np.ndarray:
        self._validate_joint_index(joint_index)
        start = 2 * joint_index
        return self.matrix[start : start + 2]

    def sliding_row_pair(self, joint_index: int) -> np.ndarray:
        self._validate_joint_index(joint_index)
        start = 2 * self.joint_count + 2 * joint_index
        return self.matrix[start : start + 2]

    def as_joint_triples(self, row_index: int) -> np.ndarray:
        return self.matrix[row_index].reshape((self.joint_count, 3))

    def transform_joint_loads(self, loads: np.ndarray) -> np.ndarray:
        expected = (self.joint_count, 3)
        if loads.shape != expected:
            raise ValueError(f"loads shape {loads.shape} does not match expected {expected}")
        return self.matrix @ loads.ravel()

    def _validate_joint_index(self, joint_index: int) -> None:
        if not 0 <= joint_index < self.joint_count:
            raise IndexError(f"joint index {joint_index} outside 0..{self.joint_count - 1}")


def read_ab_dump(path: str | Path, block_count: int) -> ABDump:
    dump_path = Path(path)
    data = dump_path.read_bytes()
    if len(data) % 4:
        raise ValueError(f"{dump_path} is not a float32 MELB AB dump")

    joints = block_count + 1
    shape = (4 * joints, 3 * joints)
    expected_values = shape[0] * shape[1]
    actual_values = len(data) // 4
    if actual_values != expected_values:
        raise ValueError(
            f"{dump_path} has {actual_values} float32 values, expected {expected_values} "
            f"for {block_count} blocks"
        )

    values = np.array(struct.unpack("<" + "f" * actual_values, data), dtype=float)
    return ABDump(path=dump_path, block_count=block_count, matrix=values.reshape(shape))

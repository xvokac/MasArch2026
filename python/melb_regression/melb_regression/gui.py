from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import traceback

import numpy as np

from .builder import (
    PI,
    IterationResult,
    MelbInput,
    MelbSolveError,
    PointLoad,
    read_melb_input,
    solve_melb_iterations,
    write_melb_input,
)
from .output import write_melb_outputs_for_data


def main() -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1280, 820)
    window.show()
    return app.exec()


class MainWindow:  # resolved lazily so importing this module does not require PySide6
    def __new__(cls):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeySequence, QShortcut
        from PySide6.QtWidgets import (
            QAbstractItemView,
            QApplication,
            QComboBox,
            QDoubleSpinBox,
            QFileDialog,
            QFrame,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QScrollArea,
            QSplitter,
            QSpinBox,
            QTableWidget,
            QTableWidgetItem,
            QTabWidget,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure

        class _MainWindow(QMainWindow):
            def __init__(self) -> None:
                super().__init__()
                self.setWindowTitle("MasArch Python")
                self.input_path: Path | None = None
                self.data: MelbInput | None = None
                self.result: IterationResult | None = None

                self.path_edit = QLineEdit()
                self.path_edit.setReadOnly(True)
                open_button = QPushButton("Otevrit .in")
                open_button.clicked.connect(self.open_input)
                new_button = QPushButton("Nove zadani")
                new_button.clicked.connect(self.new_input)
                save_button = QPushButton("Ulozit .in")
                save_button.clicked.connect(self.save_input)
                run_button = QPushButton("Vypocitat")
                run_button.clicked.connect(self.run_current)
                export_button = QPushButton("Export txt/out")
                export_button.clicked.connect(self.export_outputs)

                self.summary_text = QTextEdit()
                self.summary_text.setReadOnly(True)
                self.summary_text.setMinimumHeight(150)

                self.step_combo = QComboBox()
                self.step_combo.currentIndexChanged.connect(self.refresh_step_views)

                self.input_table = QTableWidget()
                self.load_editor = QTableWidget()
                self.geometry_table = QTableWidget()
                self.load_table = QTableWidget()
                self.result_table = QTableWidget()
                for table in [self.input_table, self.geometry_table, self.load_table, self.result_table]:
                    table.setAlternatingRowColors(True)
                    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                    table.setSelectionBehavior(QAbstractItemView.SelectRows)
                    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
                    self.add_copy_shortcut(table)

                self.figure = Figure(figsize=(7, 5), tight_layout=True)
                self.canvas = FigureCanvas(self.figure)

                controls = QGroupBox("Vstup")
                controls_layout = QGridLayout(controls)
                controls_layout.addWidget(QLabel("Soubor"), 0, 0)
                controls_layout.addWidget(self.path_edit, 0, 1)
                controls_layout.addWidget(open_button, 0, 2)
                controls_layout.addWidget(new_button, 1, 0)
                controls_layout.addWidget(save_button, 1, 1)
                controls_layout.addWidget(run_button, 2, 1)
                controls_layout.addWidget(export_button, 1, 2)
                controls_layout.addWidget(QLabel("Krok"), 3, 0)
                controls_layout.addWidget(self.step_combo, 3, 1, 1, 2)

                self.form_fields: dict[str, object] = {}
                form_box = self.build_form()
                form_scroll = QScrollArea()
                form_scroll.setWidgetResizable(True)
                form_scroll.setWidget(form_box)

                left_tabs = QTabWidget()
                left_tabs.addTab(form_scroll, "Formular")
                left_tabs.addTab(self.input_table, "Parametry")

                left = QFrame()
                left_layout = QVBoxLayout(left)
                left_layout.addWidget(controls)
                left_layout.addWidget(QLabel("Souhrn"))
                left_layout.addWidget(self.summary_text)
                left_layout.addWidget(left_tabs)

                tabs = QTabWidget()
                tabs.addTab(self.canvas, "Graf")
                tabs.addTab(self.result_table, "Vysledky")
                tabs.addTab(self.geometry_table, "Geometrie")
                tabs.addTab(self.load_table, "Zatizeni")

                splitter = QSplitter(Qt.Horizontal)
                splitter.addWidget(left)
                splitter.addWidget(tabs)
                splitter.setSizes([390, 890])

                root = QWidget()
                root_layout = QHBoxLayout(root)
                root_layout.addWidget(splitter)
                self.setCentralWidget(root)
                self.populate_form(self.default_input())

            def open_input(self) -> None:
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Otevrit vstup MELB",
                    r"D:\Documents\2026\MASARCH2026",
                    "MELB input (*.in *.IN);;Vsechny soubory (*.*)",
                )
                if path:
                    self.load_input(Path(path))

            def load_input(self, path: Path) -> None:
                try:
                    self.input_path = path
                    self.data = read_melb_input(path)
                    self.result = None
                    self.path_edit.setText(str(path))
                    self.populate_form(self.data)
                    self.step_combo.clear()
                    self.summary_text.setPlainText("Vstup nacten. Spustte vypocet.")
                    self.fill_input_table(self.data)
                    self.clear_result_views()
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Vstup se nepodarilo nacist", exc)

            def new_input(self) -> None:
                self.input_path = None
                self.data = self.default_input()
                self.result = None
                self.path_edit.clear()
                self.populate_form(self.data)
                self.step_combo.clear()
                self.summary_text.setPlainText("Nove zadani pripraveno. Upravte formular a spustte vypocet.")
                self.fill_input_table(self.data)
                self.clear_result_views()

            def save_input(self) -> None:
                try:
                    data = self.form_to_data()
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Zadani neni platne", exc)
                    return
                start = self.input_path if self.input_path is not None else Path.cwd() / "masarch_input.in"
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Ulozit vstup MELB",
                    str(start),
                    "MELB input (*.in *.IN);;Vsechny soubory (*.*)",
                )
                if not path:
                    return
                try:
                    saved = replace(data, path=Path(path))
                    write_melb_input(saved, path)
                    self.input_path = Path(path)
                    self.data = saved
                    self.path_edit.setText(str(path))
                    self.fill_input_table(saved)
                    QMessageBox.information(self, "Ulozeni", f"Ulozeno:\n{path}")
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Vstup se nepodarilo ulozit", exc)

            def run_current(self) -> None:
                try:
                    self.data = self.form_to_data()
                    self.fill_input_table(self.data)
                    self.result = solve_melb_iterations(self.data)
                    self.step_combo.blockSignals(True)
                    self.step_combo.clear()
                    for step in self.result.steps:
                        label = f"krok {step.index}: lambda {step.load_factor:.6f}"
                        self.step_combo.addItem(label)
                    self.step_combo.setCurrentIndex(len(self.result.steps) - 1)
                    self.step_combo.blockSignals(False)
                    self.refresh_all()
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Vypocet selhal", exc)

            def export_outputs(self) -> None:
                try:
                    data = self.form_to_data()
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Zadani neni platne", exc)
                    return
                stem = data.path.stem if data.path.name else "masarch"
                start_dir = data.path.parent if data.path.parent != Path(".") else Path.cwd()
                txt_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Ulozit detailni txt",
                    str(start_dir / f"{stem}_py.txt"),
                    "Text (*.txt);;Vsechny soubory (*.*)",
                )
                if not txt_path:
                    return
                out_path = str(Path(txt_path).with_suffix(".out"))
                try:
                    self.data = data
                    self.result = write_melb_outputs_for_data(data, txt_path, out_path)
                    QMessageBox.information(self, "Export", f"Ulozeno:\n{txt_path}\n{out_path}")
                    self.fill_input_table(data)
                    self.step_combo.blockSignals(True)
                    self.step_combo.clear()
                    for step in self.result.steps:
                        self.step_combo.addItem(f"krok {step.index}: lambda {step.load_factor:.6f}")
                    self.step_combo.setCurrentIndex(len(self.result.steps) - 1)
                    self.step_combo.blockSignals(False)
                    self.refresh_all()
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Export selhal", exc)

            def build_form(self) -> QGroupBox:
                box = QGroupBox("Zadani")
                layout = QGridLayout(box)
                rows = [
                    ("span", "Rozpeti", self.double_box(0.001, 1000.0, 3)),
                    ("rise", "Vzepeti", self.double_box(0.001, 1000.0, 3)),
                    ("geom_code", "Geometrie", self.combo_box([(1, "1 kruznice"), (2, "2 parabola")])),
                    ("thickness", "Tloustka D", self.double_box(0.001, 100.0, 4)),
                    ("masonry_unit_weight", "Obj. tiha klenby", self.double_box(0.0, 1000.0, 3)),
                    ("sliding_coefficient", "s_b", self.double_box(0.0, 100.0, 4)),
                    ("block_count", "Pocet bloku N", self.spin_box(2, 500)),
                    ("fill_height", "Vyska zasypu", self.double_box(0.0, 1000.0, 3)),
                    ("fill_unit_weight", "Obj. tiha zasypu", self.double_box(0.0, 1000.0, 3)),
                    ("q_code", "Q_CODE", self.combo_box([(0, "0 bez roznosu"), (1, "1 roznos"), (2, "2 Boussinesq")])),
                    ("fill_spread_angle", "Uhel roznosu [deg]", self.double_box(0.0, 89.0, 3)),
                    ("k_code", "K_CODE", self.combo_box([(0, "0 bez zemniho tlaku"), (1, "1 konstantni"), (2, "2 iteracni")])),
                    ("k0", "K0", self.double_box(0.0, 100.0, 4)),
                    ("ka", "Ka", self.double_box(0.0, 100.0, 4)),
                    ("kp", "Kp", self.double_box(0.0, 100.0, 4)),
                    ("k_code_q", "K_CODE_q", self.combo_box([(0, "0 bez Q"), (1, "1 vcetne Q")])),
                    ("d_code", "d_CODE", self.combo_box([
                        (0, "0 - infinitní pevnost"),
                        (1, "1 - pevnost fd (Crisfield)"),
                        (2, "2 - pevnost fd (Livensley)"),
                        (3, "3 - jádro průřezu (D/3)"),
                        (4, "4 - dle interakčního diagramu"),
                    ])),
                    ("d_sigma", "d_sigma", self.double_box(0.0, 1.0e9, 3)),
                ]
                for row_index, (key, label, widget) in enumerate(rows):
                    self.form_fields[key] = widget
                    layout.addWidget(QLabel(label), row_index, 0)
                    layout.addWidget(widget, row_index, 1)

                self.form_fields["interaction_file"] = QLineEdit()
                layout.addWidget(QLabel("Interakcni soubor"), len(rows), 0)
                layout.addWidget(self.form_fields["interaction_file"], len(rows), 1)

                load_buttons = QHBoxLayout()
                add_load = QPushButton("Pridat silu")
                remove_load = QPushButton("Odebrat silu")
                add_load.clicked.connect(self.add_load_row)
                remove_load.clicked.connect(self.remove_load_row)
                load_buttons.addWidget(add_load)
                load_buttons.addWidget(remove_load)

                self.load_editor.setColumnCount(3)
                self.load_editor.setHorizontalHeaderLabels(["x", "F", "sirka"])
                self.load_editor.setSelectionBehavior(QAbstractItemView.SelectRows)
                self.load_editor.setSelectionMode(QAbstractItemView.ExtendedSelection)
                self.load_editor.setMinimumHeight(120)
                self.add_copy_shortcut(self.load_editor)

                load_row = len(rows) + 1
                layout.addWidget(QLabel("Bodove sily"), load_row, 0, 1, 2)
                layout.addLayout(load_buttons, load_row + 1, 0, 1, 2)
                layout.addWidget(self.load_editor, load_row + 2, 0, 1, 2)
                return box

            def double_box(self, minimum: float, maximum: float, decimals: int) -> QDoubleSpinBox:
                box = QDoubleSpinBox()
                box.setRange(minimum, maximum)
                box.setDecimals(decimals)
                box.setSingleStep(10 ** -decimals)
                return box

            def spin_box(self, minimum: int, maximum: int) -> QSpinBox:
                box = QSpinBox()
                box.setRange(minimum, maximum)
                return box

            def combo_box(self, items: list[tuple[int, str]]) -> QComboBox:
                box = QComboBox()
                for value, label in items:
                    box.addItem(label, value)
                return box

            def set_combo_value(self, key: str, value: int) -> None:
                combo = self.form_fields[key]
                index = combo.findData(value)
                combo.setCurrentIndex(index if index >= 0 else 0)

            def combo_value(self, key: str) -> int:
                return int(self.form_fields[key].currentData())

            def populate_form(self, data: MelbInput) -> None:
                self.form_fields["span"].setValue(data.span)
                self.form_fields["rise"].setValue(data.rise)
                self.set_combo_value("geom_code", data.geom_code)
                self.form_fields["thickness"].setValue(data.thickness)
                self.form_fields["masonry_unit_weight"].setValue(data.masonry_unit_weight)
                self.form_fields["sliding_coefficient"].setValue(data.sliding_coefficient)
                self.form_fields["block_count"].setValue(data.block_count)
                self.form_fields["fill_height"].setValue(data.fill_height)
                self.form_fields["fill_unit_weight"].setValue(data.fill_unit_weight)
                self.set_combo_value("q_code", data.q_code)
                self.form_fields["fill_spread_angle"].setValue(data.fill_spread_angle * 180.0 / PI)
                self.set_combo_value("k_code", int(data.k_fill[0]))
                self.form_fields["k0"].setValue(data.k_fill[1])
                self.form_fields["ka"].setValue(data.k_fill[2])
                self.form_fields["kp"].setValue(data.k_fill[3])
                self.set_combo_value("k_code_q", int(data.k_fill[4]))
                self.set_combo_value("d_code", data.d_code)
                self.form_fields["d_sigma"].setValue(data.d_sigma)
                self.form_fields["interaction_file"].setText(data.interaction_file)
                self.load_editor.setRowCount(0)
                for load in data.point_loads:
                    self.add_load_row(load)
                self.load_editor.resizeColumnsToContents()

            def form_to_data(self) -> MelbInput:
                path = self.input_path if self.input_path is not None else Path("masarch_input.in")
                loads = []
                for row in range(self.load_editor.rowCount()):
                    values = []
                    empty = True
                    for column in range(3):
                        item = self.load_editor.item(row, column)
                        text = item.text().strip() if item is not None else ""
                        if text:
                            empty = False
                        values.append(float(text.replace(",", ".")) if text else 0.0)
                    if not empty:
                        loads.append(PointLoad(values[0], values[1], values[2]))
                return MelbInput(
                    path=path,
                    span=self.form_fields["span"].value(),
                    rise=self.form_fields["rise"].value(),
                    geom_code=self.combo_value("geom_code"),
                    thickness=self.form_fields["thickness"].value(),
                    masonry_unit_weight=self.form_fields["masonry_unit_weight"].value(),
                    sliding_coefficient=self.form_fields["sliding_coefficient"].value(),
                    block_count=self.form_fields["block_count"].value(),
                    point_loads=tuple(loads),
                    fill_height=self.form_fields["fill_height"].value(),
                    fill_unit_weight=self.form_fields["fill_unit_weight"].value(),
                    q_code=self.combo_value("q_code"),
                    fill_spread_angle=self.form_fields["fill_spread_angle"].value() * PI / 180.0,
                    k_fill=(
                        float(self.combo_value("k_code")),
                        self.form_fields["k0"].value(),
                        self.form_fields["ka"].value(),
                        self.form_fields["kp"].value(),
                        float(self.combo_value("k_code_q")),
                    ),
                    d_code=self.combo_value("d_code"),
                    d_sigma=self.form_fields["d_sigma"].value(),
                    interaction_file=self.form_fields["interaction_file"].text().strip() or "inter.txt",
                )

            def add_load_row(self, load: PointLoad | None = None) -> None:
                row = self.load_editor.rowCount()
                self.load_editor.insertRow(row)
                values = (load.x, load.force, load.width) if load is not None else (0.0, 0.0, 0.0)
                for column, value in enumerate(values):
                    item = QTableWidgetItem(self.format_cell(value))
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.load_editor.setItem(row, column, item)

            def remove_load_row(self) -> None:
                rows = sorted({index.row() for index in self.load_editor.selectedIndexes()}, reverse=True)
                if not rows and self.load_editor.rowCount():
                    rows = [self.load_editor.rowCount() - 1]
                for row in rows:
                    self.load_editor.removeRow(row)

            def default_input(self) -> MelbInput:
                return MelbInput(
                    path=Path("masarch_input.in"),
                    span=3.0,
                    rise=1.0,
                    geom_code=1,
                    thickness=0.3,
                    masonry_unit_weight=22.0,
                    sliding_coefficient=0.6,
                    block_count=25,
                    point_loads=(PointLoad(1.5, 1.0, 0.2),),
                    fill_height=0.5,
                    fill_unit_weight=18.0,
                    q_code=0,
                    fill_spread_angle=30.0 * PI / 180.0,
                    k_fill=(0.0, 0.5, 0.333333, 3.0, 0.0),
                    d_code=0,
                    d_sigma=2000.0,
                    interaction_file="inter.txt",
                )

            def refresh_all(self) -> None:
                if self.data is None or self.result is None:
                    return
                self.fill_summary(self.data, self.result)
                self.refresh_step_views()

            def refresh_step_views(self) -> None:
                if self.data is None or self.result is None or not self.result.steps:
                    return
                index = self.step_combo.currentIndex()
                if index < 0:
                    index = len(self.result.steps) - 1
                step = self.result.steps[index]
                self.fill_geometry_table(step.prepared.intrados_extrados)
                self.fill_load_table(step)
                self.fill_result_table(step)
                self.plot_step(step)

            def clear_result_views(self) -> None:
                self.geometry_table.clear()
                self.load_table.clear()
                self.result_table.clear()
                self.figure.clear()
                self.canvas.draw_idle()

            def fill_summary(self, data: MelbInput, result: IterationResult) -> None:
                final = result.final
                active = np.flatnonzero(final.mechanism > 1e-5) + 1
                lines = [
                    f"Soubor: {data.path.name}",
                    f"N = {data.block_count}",
                    f"geom_CODE = {data.geom_code}, Q_CODE = {data.q_code}, K_CODE = {data.k_fill[0]:.0f}, d_CODE = {data.d_code}",
                    f"Kroky vypoctu = {len(result.steps)}",
                    f"lambda = {final.load_factor:.6f}",
                    "Aktivni deformace: " + (" ".join(str(value) for value in active) if len(active) else "-"),
                ]
                self.summary_text.setPlainText("\n".join(lines))

            def fill_input_table(self, data: MelbInput) -> None:
                rows = [
                    ("rozpeti", data.span),
                    ("vzepeti", data.rise),
                    ("geom_CODE", data.geom_code),
                    ("tloustka", data.thickness),
                    ("objemova tiha klenby", data.masonry_unit_weight),
                    ("s_b", data.sliding_coefficient),
                    ("N", data.block_count),
                    ("pocet sil", len(data.point_loads)),
                    ("HFill", data.fill_height),
                    ("GamaFill", data.fill_unit_weight),
                    ("Q_CODE", data.q_code),
                    ("AlfaFill [rad]", data.fill_spread_angle),
                    ("K_CODE", data.k_fill[0]),
                    ("K0", data.k_fill[1]),
                    ("Ka", data.k_fill[2]),
                    ("Kp", data.k_fill[3]),
                    ("K_CODE_q", data.k_fill[4]),
                    ("d_CODE", data.d_code),
                    ("d_sigma", data.d_sigma),
                ]
                self.set_table(self.input_table, ["parametr", "hodnota"], rows)

            def fill_geometry_table(self, values: np.ndarray) -> None:
                rows = [(i, *values[i]) for i in range(len(values))]
                self.set_table(self.geometry_table, ["i", "X_int", "Y_int", "X_ext", "Y_ext"], rows)

            def fill_load_table(self, step: IterationStep) -> None:
                p = step.prepared
                rows = []
                for i in range(len(p.transformed_masonry)):
                    rows.append(
                        (
                            i,
                            p.transformed_masonry[i, 1],
                            p.transformed_fill[i, 1],
                            p.transformed_external[i, 1],
                            p.transformed_masonry[i, 2],
                            p.transformed_fill[i, 2],
                            p.transformed_external[i, 2],
                        )
                    )
                self.set_table(self.load_table, ["i", "G_y", "Fill_y", "Q_y", "G_M", "Fill_M", "Q_M"], rows)

            def fill_result_table(self, step: IterationStep) -> None:
                rows = []
                half_thickness = step.prepared.input.thickness / 2.0
                for i in range(len(step.normal_forces)):
                    normal_force = step.normal_forces[i]
                    normal_distance = step.normal_distances[i]
                    bending_moment = normal_force * (normal_distance - half_thickness)
                    rows.append((i, normal_force, normal_distance, bending_moment, step.shear_forces[i]))
                self.set_table(self.result_table, ["spara", "N", "e od horniho povrchu", "M", "T"], rows)

            def set_table(self, table: QTableWidget, headers: list[str], rows: list[tuple]) -> None:
                table.clear()
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                table.setRowCount(len(rows))
                for row_index, row in enumerate(rows):
                    for column_index, value in enumerate(row):
                        item = QTableWidgetItem(self.format_cell(value))
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        table.setItem(row_index, column_index, item)
                table.resizeColumnsToContents()

            def add_copy_shortcut(self, table: QTableWidget) -> None:
                shortcut = QShortcut(QKeySequence.Copy, table)
                shortcut.activated.connect(lambda table=table: self.copy_table_selection(table))
                table._copy_shortcut = shortcut

            def copy_table_selection(self, table: QTableWidget) -> None:
                ranges = table.selectedRanges()
                if not ranges:
                    return
                blocks = []
                for selected in ranges:
                    lines = []
                    for row in range(selected.topRow(), selected.bottomRow() + 1):
                        values = []
                        for column in range(selected.leftColumn(), selected.rightColumn() + 1):
                            item = table.item(row, column)
                            values.append(item.text() if item is not None else "")
                        lines.append("\t".join(values))
                    blocks.append("\n".join(lines))
                QApplication.clipboard().setText("\n".join(blocks))

            def plot_step(self, step: IterationStep) -> None:
                p = step.prepared
                geom = p.intrados_extrados
                intrados = geom[:, 0:2]
                extrados = geom[:, 2:4]
                pressure = self.pressure_line(step)
                active = np.flatnonzero(step.mechanism[: 2 * len(intrados)] > 1e-5)

                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.plot(intrados[:, 0], intrados[:, 1], color="#1f77b4", linewidth=2.0, label="intrados")
                ax.plot(extrados[:, 0], extrados[:, 1], color="#1f77b4", linewidth=2.0, label="extrados")
                self.plot_fill_surface(ax, step.prepared.input, extrados)
                self.plot_input_loads(ax, step.prepared.input, extrados)
                for i in range(len(intrados)):
                    ax.plot([intrados[i, 0], extrados[i, 0]], [intrados[i, 1], extrados[i, 1]], color="#b8c2cc", linewidth=0.7)
                self.plot_sliding_joints(ax, step, intrados, extrados)
                ax.plot(pressure[:, 0], pressure[:, 1], color="#d62728", linewidth=1.8, marker="o", markersize=3, label="N")
                for variable in active:
                    joint = variable // 2
                    point = intrados[joint] if variable % 2 == 0 else extrados[joint]
                    ax.scatter([point[0]], [point[1]], s=60, color="#111111", zorder=5)
                self.plot_loads(ax, p.external_loads)
                ax.set_aspect("equal", adjustable="box")
                ax.grid(True, color="#e2e8f0")
                ax.set_title(f"lambda = {step.load_factor:.6f}")
                ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0, fontsize=8)
                self.figure.subplots_adjust(right=0.76)
                self.canvas.draw_idle()

            def plot_fill_surface(self, ax, data: MelbInput, extrados: np.ndarray) -> None:
                if data.fill_height <= 0.0:
                    return
                top_y = data.rise + data.thickness + data.fill_height
                x_min = float(np.min(extrados[:, 0]))
                x_max = float(np.max(extrados[:, 0]))
                ax.fill_between(
                    extrados[:, 0],
                    extrados[:, 1],
                    top_y,
                    where=top_y >= extrados[:, 1],
                    color="#d8c6a3",
                    alpha=0.28,
                    linewidth=0.0,
                    label="nadnasyp",
                )
                ax.plot(
                    [x_min, x_max],
                    [top_y, top_y],
                    color="#8a6f3d",
                    linewidth=1.2,
                    linestyle="--",
                    label="horni okraj nadnasypu",
                )

            def plot_input_loads(self, ax, data: MelbInput, extrados: np.ndarray) -> None:
                if not data.point_loads:
                    return
                top_y = data.rise + data.thickness + data.fill_height
                y_min = float(min(np.min(extrados[:, 1]), top_y))
                y_span = max(abs(top_y - y_min), data.thickness, 1.0)
                arrow_length = 0.10 * y_span
                width_floor = 0.015 * max(float(np.ptp(extrados[:, 0])), data.span, 1.0)
                for index, load in enumerate(data.point_loads):
                    half_width = max(load.width / 2.0, width_floor)
                    label = "zatizeni na povrchu" if index == 0 else None
                    ax.plot(
                        [load.x - half_width, load.x + half_width],
                        [top_y, top_y],
                        color="#6f3fa0",
                        linewidth=3.0,
                        solid_capstyle="butt",
                        label=label,
                    )
                    ax.arrow(
                        load.x,
                        top_y + arrow_length,
                        0.0,
                        -arrow_length,
                        width=0.0025,
                        head_width=0.035,
                        head_length=0.035,
                        color="#6f3fa0",
                        length_includes_head=True,
                    )

            def plot_sliding_joints(self, ax, step: IterationStep, intrados: np.ndarray, extrados: np.ndarray) -> None:
                joint_count = len(intrados)
                offset = 2 * joint_count
                if step.prepared.input.sliding_coefficient <= 0.0 or len(step.mechanism) <= offset:
                    return
                sliding = step.mechanism[offset : offset + 2 * joint_count]
                active_joints = sorted({index // 2 for index, value in enumerate(sliding) if abs(value) > 1e-5})
                for position, joint in enumerate(active_joints):
                    if joint >= joint_count:
                        continue
                    ax.plot(
                        [intrados[joint, 0], extrados[joint, 0]],
                        [intrados[joint, 1], extrados[joint, 1]],
                        color="#f28e2b",
                        linewidth=4.0,
                        solid_capstyle="round",
                        label="smykova porucha" if position == 0 else None,
                        zorder=6,
                    )

            def pressure_line(self, step: IterationStep) -> np.ndarray:
                geom = step.prepared.intrados_extrados
                intrados = geom[:, 0:2]
                extrados = geom[:, 2:4]
                thickness = np.linalg.norm(intrados - extrados, axis=1)
                ratio = np.divide(step.normal_distances, thickness, out=np.zeros_like(step.normal_distances), where=thickness > 0)
                ratio = np.clip(ratio, 0.0, 1.0)
                return extrados + ratio[:, None] * (intrados - extrados)

            def plot_loads(self, ax, loads: np.ndarray) -> None:
                nonzero = loads[np.abs(loads[:, 2]) > 1e-10]
                if len(nonzero) == 0:
                    return
                y_span = ax.get_ylim()[1] - ax.get_ylim()[0] if ax.get_ylim()[1] != ax.get_ylim()[0] else 1.0
                length = 0.08 * abs(y_span)
                for x, y, force in nonzero:
                    ax.arrow(x, y + length, 0.0, -length, width=0.003, head_width=0.025, head_length=0.025, color="#2ca02c", length_includes_head=True)

            def format_cell(self, value) -> str:
                if isinstance(value, (int, np.integer)):
                    return str(int(value))
                if isinstance(value, (float, np.floating)):
                    return f"{float(value):.6g}"
                return str(value)

            def show_error(self, title: str, exc: Exception) -> None:
                if isinstance(exc, MelbSolveError):
                    QMessageBox.warning(self, title, str(exc))
                    return
                QMessageBox.critical(self, title, f"{exc}\n\n{traceback.format_exc()}")

        return _MainWindow()


if __name__ == "__main__":
    raise SystemExit(main())

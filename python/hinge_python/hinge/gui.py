from __future__ import annotations

from pathlib import Path
import sys
import traceback

from .core import Diagram, compute_diagram, parse_input, render_output
from .plotting import plot_diagram


METHOD_PARAMETERS = {
    1: [
        ("b", "Sirka b"),
        ("h", "Vyska h"),
        ("sigma_m", "Pevnost sigma_m"),
        ("eps_m", "Pretvoreni eps_m"),
        ("lambda", "Lambda"),
        ("k", "Exponent k"),
    ],
    2: [
        ("b", "Sirka b"),
        ("h", "Vyska h"),
        ("sigma", "Pevnost sigma"),
    ],
    3: [
        ("b", "Sirka b"),
        ("h", "Vyska h"),
        ("sigma_m", "Pevnost sigma_m"),
        ("eps_m", "Pretvoreni eps_m"),
        ("lambda", "Lambda"),
    ],
    4: [
        ("b", "Sirka b"),
        ("h", "Vyska h"),
        ("sigma", "Pevnost sigma"),
    ],
}


DEFAULT_VALUES = {
    1: [1.0, 1.0, 1.0, 0.002, 2.0, 2.0],
    2: [1.0, 1.0, 1.0],
    3: [1.0, 1.0, 1.0, 0.002, 2.0],
    4: [1.0, 1.0, 1.0],
}


def main() -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1180, 760)
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
            QSpinBox,
            QSplitter,
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
                self.setWindowTitle("HINGE Python")
                self.input_path: Path | None = None
                self.diagram: Diagram | None = None

                self.path_edit = QLineEdit()
                self.path_edit.setReadOnly(True)

                open_button = QPushButton("Otevrit vstup")
                open_button.clicked.connect(self.open_input)
                new_button = QPushButton("Nove zadani")
                new_button.clicked.connect(self.new_input)
                save_button = QPushButton("Ulozit vstup")
                save_button.clicked.connect(self.save_input)
                run_button = QPushButton("Vypocitat")
                run_button.clicked.connect(self.run_current)
                export_button = QPushButton("Export out")
                export_button.clicked.connect(self.export_output)
                plot_button = QPushButton("Export graf")
                plot_button.clicked.connect(self.export_plot)

                self.method_combo = QComboBox()
                self.method_combo.addItem("1 - nelinearni material", 1)
                self.method_combo.addItem("2 - parabolicky diagram", 2)
                self.method_combo.addItem("3 - bilinearni material", 3)
                self.method_combo.addItem("4 - upraveny parabolicky diagram", 4)
                self.method_combo.currentIndexChanged.connect(self.refresh_parameter_form)

                self.n_spin = QSpinBox()
                self.n_spin.setRange(1, 10000)
                self.n_spin.setValue(20)

                self.param_labels: list[QLabel] = []
                self.param_boxes: list[QDoubleSpinBox] = []

                controls = QGroupBox("Vstup")
                controls_layout = QGridLayout(controls)
                controls_layout.addWidget(QLabel("Soubor"), 0, 0)
                controls_layout.addWidget(self.path_edit, 0, 1, 1, 3)
                controls_layout.addWidget(open_button, 0, 4)
                controls_layout.addWidget(new_button, 1, 0)
                controls_layout.addWidget(save_button, 1, 1)
                controls_layout.addWidget(run_button, 1, 2)
                controls_layout.addWidget(export_button, 1, 3)
                controls_layout.addWidget(plot_button, 1, 4)

                form = QGroupBox("Zadani")
                form_layout = QGridLayout(form)
                form_layout.addWidget(QLabel("METHOD"), 0, 0)
                form_layout.addWidget(self.method_combo, 0, 1)
                form_layout.addWidget(QLabel("N"), 1, 0)
                form_layout.addWidget(self.n_spin, 1, 1)
                for row in range(6):
                    label = QLabel()
                    box = self.double_box()
                    self.param_labels.append(label)
                    self.param_boxes.append(box)
                    form_layout.addWidget(label, row + 2, 0)
                    form_layout.addWidget(box, row + 2, 1)

                self.summary_text = QTextEdit()
                self.summary_text.setReadOnly(True)
                self.summary_text.setMinimumHeight(120)

                self.result_table = QTableWidget()
                self.result_table.setAlternatingRowColors(True)
                self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                self.result_table.setSelectionBehavior(QAbstractItemView.SelectItems)
                self.result_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
                self.add_copy_shortcut(self.result_table)

                self.output_text = QTextEdit()
                self.output_text.setReadOnly(True)

                self.figure = Figure(figsize=(7, 5), tight_layout=True)
                self.canvas = FigureCanvas(self.figure)

                left = QFrame()
                left_layout = QVBoxLayout(left)
                left_layout.addWidget(controls)
                left_layout.addWidget(form)
                left_layout.addWidget(QLabel("Souhrn"))
                left_layout.addWidget(self.summary_text)

                tabs = QTabWidget()
                tabs.addTab(self.canvas, "Graf")
                tabs.addTab(self.result_table, "Vysledky")
                tabs.addTab(self.output_text, "OUT")

                splitter = QSplitter(Qt.Horizontal)
                splitter.addWidget(left)
                splitter.addWidget(tabs)
                splitter.setSizes([390, 790])

                root = QWidget()
                root_layout = QHBoxLayout(root)
                root_layout.addWidget(splitter)
                self.setCentralWidget(root)

                self.refresh_parameter_form()
                self.run_current()

            def double_box(self) -> QDoubleSpinBox:
                box = QDoubleSpinBox()
                box.setRange(-1.0e12, 1.0e12)
                box.setDecimals(8)
                box.setSingleStep(0.1)
                return box

            def open_input(self) -> None:
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Otevrit vstup HINGE",
                    r"D:\Documents\2026\MASARCH2026",
                    "HINGE input (*.txt *.TXT *.in *.IN);;Vsechny soubory (*.*)",
                )
                if path:
                    self.load_input(Path(path))

            def load_input(self, path: Path) -> None:
                try:
                    method, n, values = parse_input(path)
                    self.input_path = path
                    self.path_edit.setText(str(path))
                    self.set_method(method)
                    self.n_spin.setValue(n)
                    self.set_values(values)
                    self.run_current()
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Vstup se nepodarilo nacist", exc)

            def new_input(self) -> None:
                self.input_path = None
                self.path_edit.clear()
                self.set_method(2)
                self.n_spin.setValue(20)
                self.set_values(DEFAULT_VALUES[2])
                self.run_current()

            def save_input(self) -> None:
                start = self.input_path if self.input_path is not None else Path.cwd() / "hinge_input.txt"
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Ulozit vstup HINGE",
                    str(start),
                    "Text (*.txt);;Vsechny soubory (*.*)",
                )
                if not path:
                    return
                try:
                    Path(path).write_text(self.format_input(Path(path).name), encoding="cp1250")
                    self.input_path = Path(path)
                    self.path_edit.setText(str(path))
                    QMessageBox.information(self, "Ulozeni", f"Ulozeno:\n{path}")
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Vstup se nepodarilo ulozit", exc)

            def run_current(self) -> None:
                try:
                    method, n, values = self.form_values()
                    self.diagram = compute_diagram(method, n, values)
                    self.fill_summary(self.diagram)
                    self.fill_result_table(self.diagram)
                    self.output_text.setPlainText(render_output(self.diagram))
                    self.plot_diagram(self.diagram)
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Vypocet selhal", exc)

            def export_output(self) -> None:
                if self.diagram is None:
                    return
                stem = self.input_path.stem if self.input_path is not None else "hinge"
                start_dir = self.input_path.parent if self.input_path is not None else Path.cwd()
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Ulozit vystup HINGE",
                    str(start_dir / f"{stem}.out"),
                    "OUT (*.out);;Text (*.txt);;Vsechny soubory (*.*)",
                )
                if not path:
                    return
                try:
                    Path(path).write_text(render_output(self.diagram), encoding="cp1250")
                    QMessageBox.information(self, "Export", f"Ulozeno:\n{path}")
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Export selhal", exc)

            def export_plot(self) -> None:
                if self.diagram is None:
                    return
                stem = self.input_path.stem if self.input_path is not None else "hinge"
                start_dir = self.input_path.parent if self.input_path is not None else Path.cwd()
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Ulozit graf HINGE",
                    str(start_dir / f"{stem}.png"),
                    "Obrazek (*.png *.svg *.pdf);;Vsechny soubory (*.*)",
                )
                if not path:
                    return
                try:
                    plot_diagram(self.diagram, path)
                    QMessageBox.information(self, "Export", f"Ulozeno:\n{path}")
                except Exception as exc:  # noqa: BLE001
                    self.show_error("Export grafu selhal", exc)

            def set_method(self, method: int) -> None:
                index = self.method_combo.findData(method)
                self.method_combo.setCurrentIndex(index if index >= 0 else 0)

            def current_method(self) -> int:
                return int(self.method_combo.currentData())

            def refresh_parameter_form(self) -> None:
                method = self.current_method()
                defaults = DEFAULT_VALUES[method]
                parameters = METHOD_PARAMETERS[method]
                for index, box in enumerate(self.param_boxes):
                    if index < len(parameters):
                        self.param_labels[index].setText(parameters[index][1])
                        self.param_labels[index].show()
                        box.show()
                        if box.value() == 0.0:
                            box.setValue(defaults[index])
                    else:
                        self.param_labels[index].hide()
                        box.hide()

            def set_values(self, values: list[float]) -> None:
                method = self.current_method()
                defaults = DEFAULT_VALUES[method]
                for index, box in enumerate(self.param_boxes):
                    if index < len(defaults):
                        value = values[index] if index < len(values) else defaults[index]
                        box.setValue(value)

            def form_values(self) -> tuple[int, int, list[float]]:
                method = self.current_method()
                count = len(METHOD_PARAMETERS[method])
                values = [self.param_boxes[index].value() for index in range(count)]
                return method, self.n_spin.value(), values

            def format_input(self, title: str) -> str:
                method, n, values = self.form_values()
                lines = [title, str(method), str(n)]
                lines.extend(self.format_number(value) for value in values)
                return "\n".join(lines) + "\n"

            def fill_summary(self, diagram: Diagram) -> None:
                lines = [
                    f"METHOD = {diagram.method}",
                    f"N = {diagram.n}",
                    f"Max N = {diagram.max_axial_force:.6g}",
                    f"Pocet bodu = {len(diagram.points)}",
                ]
                self.summary_text.setPlainText("\n".join(lines))

            def fill_result_table(self, diagram: Diagram) -> None:
                rows = [
                    (index, point.axial_force, point.moment)
                    for index, point in enumerate(diagram.points)
                ]
                self.set_table(self.result_table, ["i", "N", "M"], rows)

            def set_table(self, table: QTableWidget, headers: list[str], rows: list[tuple]) -> None:
                table.clear()
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                table.setRowCount(len(rows))
                for row_index, row in enumerate(rows):
                    for column_index, value in enumerate(row):
                        item = QTableWidgetItem(self.format_number(value))
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

            def plot_diagram(self, diagram: Diagram) -> None:
                moments = [point.moment for point in diagram.points]
                axial_forces = [point.axial_force for point in diagram.points]
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.plot(moments, axial_forces, color="#1f5a7a", linewidth=2.2)
                ax.scatter(moments, axial_forces, s=14, color="#d07a2d", zorder=3)
                ax.set_title(f"Interakcni diagram - METHOD={diagram.method}")
                ax.set_xlabel("Moment M")
                ax.set_ylabel("Normalova sila N")
                ax.grid(True, color="#d7dde2", linewidth=0.7)
                ax.set_xlim(left=0)
                ax.set_ylim(bottom=0)
                self.canvas.draw_idle()

            def format_number(self, value) -> str:
                if isinstance(value, int):
                    return str(value)
                return f"{float(value):.6g}"

            def show_error(self, title: str, exc: Exception) -> None:
                QMessageBox.critical(self, title, f"{exc}\n\n{traceback.format_exc()}")

        return _MainWindow()


if __name__ == "__main__":
    raise SystemExit(main())

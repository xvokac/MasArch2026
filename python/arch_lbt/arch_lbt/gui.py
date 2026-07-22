from __future__ import annotations

from pathlib import Path
import sys
import textwrap
import traceback

from .core import (
    ArchLBTInput,
    PointLoad,
    build_model,
    format_arch_lbt_input,
    format_model_report,
    lbt_input_from_melb,
    read_arch_lbt_input,
    read_model,
    solve_parabolic_interaction_lower_bound,
    write_arch_lbt_input,
)
from .plotting import plot_arch_view, plot_interaction_view, plot_shear_view


def main() -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1320, 860)
    window.show()
    return app.exec()


class MainWindow:
    def __new__(cls):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
        from PySide6.QtWidgets import (
            QAbstractItemView,
            QApplication,
            QComboBox,
            QDoubleSpinBox,
            QFileDialog,
            QFormLayout,
            QFrame,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QScrollArea,
            QSizePolicy,
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
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.figure import Figure
        import numpy as np

        class _MainWindow(QMainWindow):
            def __init__(self) -> None:
                super().__init__()
                self.setWindowTitle("ArchLBT")
                self.input_path: Path | None = None
                self.data: ArchLBTInput = self.default_input()
                self.model = None
                self.result = None

                self.path_edit = QLineEdit()
                self.path_edit.setReadOnly(True)
                open_button = QPushButton("Otevrit")
                open_button.clicked.connect(self.open_input)
                save_button = QPushButton("Ulozit LBT")
                save_button.clicked.connect(self.save_input)
                solve_button = QPushButton("Vypocitat")
                solve_button.clicked.connect(self.solve_current)
                copy_tab_button = QPushButton("Kopirovat kartu")
                copy_tab_button.clicked.connect(self.copy_current_tab)
                export_pdf_button = QPushButton("Export PDF")
                export_pdf_button.clicked.connect(self.export_pdf)
                add_load_button = QPushButton("Pridat zatizeni")
                add_load_button.clicked.connect(lambda: self.add_load_row())
                remove_load_button = QPushButton("Odebrat zatizeni")
                remove_load_button.clicked.connect(self.remove_selected_loads)

                top = QHBoxLayout()
                top.addWidget(QLabel("Soubor:"))
                top.addWidget(self.path_edit, 1)
                top.addWidget(open_button)
                top.addWidget(save_button)
                top.addWidget(solve_button)
                top.addWidget(copy_tab_button)
                top.addWidget(export_pdf_button)

                self.fields: dict[str, object] = {}
                form = QFormLayout()
                form.setRowWrapPolicy(QFormLayout.WrapLongRows)
                form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
                form.addRow("Rozpeti", self.double_box("span", 0.0, 1.0e6, 6))
                form.addRow("Vzepeti", self.double_box("rise", 0.0, 1.0e6, 6))
                self.geom_combo = QComboBox()
                self.geom_combo.addItem("1 - kruznice", 1)
                self.geom_combo.addItem("2 - parabola", 2)
                form.addRow("geom_code", self.geom_combo)
                self.extrados_combo = QComboBox()
                self.extrados_combo.addItem("normal - konstantni tloustka", "normal")
                self.extrados_combo.addItem("horizontal - svisle spary", "horizontal")
                self.extrados_combo.addItem("horizontal_width_radial_joints - radialni spary", "horizontal_width_radial_joints")
                form.addRow("extrados_mode", self.extrados_combo)
                form.addRow("Tloustka D", self.double_box("thickness", 0.0, 1.0e6, 6))
                form.addRow("Sirka pasu b", self.double_box("arch_width", 0.0, 1.0e6, 6))
                form.addRow("Objemova tiha zdiva (napr. kN/m3)", self.double_box("masonry_unit_weight", 0.0, 1.0e6, 6))
                form.addRow("Pocet dilku", self.spin_box("block_count", 1, 10000))
                form.addRow("Vyska nadnasypu", self.double_box("fill_height", 0.0, 1.0e6, 6))
                form.addRow("Objemova tiha nadnasypu (napr. kN/m3)", self.double_box("fill_unit_weight", 0.0, 1.0e6, 6))
                self.q_combo = QComboBox()
                self.q_combo.addItem("0 - bez rozneseni", 0)
                self.q_combo.addItem("1 - rozneseni nadnasypem", 1)
                form.addRow("q_code", self.q_combo)
                form.addRow("Uhel rozneseni [deg]", self.double_box("fill_spread_angle_deg", -89.0, 89.0, 6))
                form.addRow("Soucin. treni mu", self.double_box("friction_coefficient", 0.0, 10.0, 6))
                form.addRow("Pevnost fc", self.double_box("compression_strength", 0.0, 1.0e9, 6))

                self.loads_table = QTableWidget(0, 3)
                self.loads_table.setHorizontalHeaderLabels(["x", "sila F", "sirka"])
                self.loads_table.setSelectionBehavior(QAbstractItemView.SelectRows)
                self.loads_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
                load_buttons = QHBoxLayout()
                load_buttons.addWidget(add_load_button)
                load_buttons.addWidget(remove_load_button)
                load_buttons.addStretch(1)

                left_inner = QWidget()
                left_layout = QVBoxLayout(left_inner)
                left_layout.addLayout(form)
                units_note = QLabel("Povrchove zatizeni F se zadava jako celkova sila na delku zatizeni, jiz se zapoctenou sirkou klenby, napr. kN.")
                units_note.setWordWrap(True)
                left_layout.addWidget(units_note)
                left_layout.addWidget(QLabel("Povrchova zatizeni"))
                left_layout.addWidget(self.loads_table)
                left_layout.addLayout(load_buttons)
                left_layout.addStretch(1)

                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setWidget(left_inner)
                scroll.setFrameShape(QFrame.NoFrame)
                scroll.setMinimumWidth(450)

                self.status_label = QLabel()
                self.report_edit = QTextEdit()
                self.report_edit.setReadOnly(True)
                self.result_table = QTableWidget(0, 9)
                self.result_table.setHorizontalHeaderLabels(["rez", "xi", "yi", "xe", "ye", "N", "M", "T", "e = M/N"])
                self.result_table.setSelectionBehavior(QAbstractItemView.SelectItems)
                self.result_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

                self.arch_canvas = self.figure_canvas()
                self.mn_canvas = self.figure_canvas()
                self.nt_canvas = self.figure_canvas()

                self.tabs = QTabWidget()
                self.tabs.addTab(self.arch_canvas, "Klenba")
                self.tabs.addTab(self.mn_canvas, "M-N")
                self.tabs.addTab(self.nt_canvas, "N-T")
                self.tabs.addTab(self.result_table, "Vysledky")
                self.tabs.addTab(self.report_edit, "Report")
                QShortcut(QKeySequence.Copy, self, self.copy_current_tab)

                right = QWidget()
                right_layout = QVBoxLayout(right)
                right_layout.addWidget(self.status_label)
                right_layout.addWidget(self.tabs, 1)

                splitter = QSplitter()
                splitter.addWidget(scroll)
                splitter.addWidget(right)
                splitter.setSizes([470, 850])

                central = QWidget()
                layout = QVBoxLayout(central)
                layout.addLayout(top)
                layout.addWidget(splitter, 1)
                self.setCentralWidget(central)

                self.set_data(self.data)
                self.solve_current()

            def figure_canvas(self):
                figure = Figure(figsize=(6.8, 5.2), dpi=110)
                canvas = FigureCanvas(figure)
                canvas.axes = figure.add_subplot(111)
                return canvas

            def double_box(self, name: str, minimum: float, maximum: float, decimals: int):
                widget = QDoubleSpinBox()
                widget.setRange(minimum, maximum)
                widget.setDecimals(decimals)
                widget.setSingleStep(0.1)
                widget.setMinimumWidth(130)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.fields[name] = widget
                return widget

            def spin_box(self, name: str, minimum: int, maximum: int):
                widget = QSpinBox()
                widget.setRange(minimum, maximum)
                widget.setMinimumWidth(130)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.fields[name] = widget
                return widget

            def default_input(self) -> ArchLBTInput:
                return ArchLBTInput(
                    path=Path("untitled_lbt.in"),
                    span=3.0,
                    rise=0.75,
                    geom_code=1,
                    extrados_mode="normal",
                    thickness=0.18,
                    arch_width=1.0,
                    masonry_unit_weight=24.0,
                    block_count=25,
                    point_loads=(PointLoad(1.5, 1.0, 0.2),),
                    fill_height=0.20,
                    fill_unit_weight=20.0,
                    q_code=1,
                    fill_spread_angle=0.0,
                    friction_coefficient=0.1,
                    compression_strength=950.0,
                )

            def open_input(self) -> None:
                filename, _ = QFileDialog.getOpenFileName(self, "Otevrit vstup", "", "Input files (*.in);;All files (*)")
                if not filename:
                    return
                try:
                    model = read_model(filename)
                    self.input_path = Path(filename)
                    if self.looks_like_lbt_input(self.input_path):
                        self.set_data(read_arch_lbt_input(self.input_path))
                    else:
                        self.set_data(lbt_input_from_melb(model.input, path=self.input_path))
                    self.model = model
                    self.solve_current()
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.critical(self, "Chyba vstupu", f"{exc}\n\n{traceback.format_exc()}")

            def looks_like_lbt_input(self, path: Path) -> bool:
                text = path.read_text(encoding="utf-8")
                for line in text.splitlines():
                    stripped = line.split("#", 1)[0].split("//", 1)[0].strip()
                    if stripped:
                        return "=" in stripped
                return False

            def save_input(self) -> None:
                default_path = str(self.input_path or self.data.path or Path("klenba_lbt.in"))
                filename, _ = QFileDialog.getSaveFileName(self, "Ulozit LBT vstup jako", default_path, "Input files (*.in);;All files (*)")
                if not filename:
                    return
                try:
                    self.input_path = Path(filename)
                    data = self.collect_data(self.input_path)
                    write_arch_lbt_input(data, self.input_path)
                    self.set_data(data)
                    self.status_label.setText(f"Ulozeno: {self.input_path}")
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.critical(self, "Chyba ulozeni", str(exc))

            def solve_current(self) -> None:
                try:
                    data = self.collect_data(self.input_path or self.data.path)
                    self.data = data
                    self.model = build_model(data)
                    self.result = solve_parabolic_interaction_lower_bound(self.model)
                    input_name = Path(data.path).name
                    plot_arch_view(self.arch_canvas.axes, input_name, self.model, self.result)
                    self.arch_canvas.figure.subplots_adjust(right=0.78, top=0.72, bottom=0.10)
                    self.arch_canvas.draw()
                    plot_interaction_view(self.mn_canvas.axes, input_name, self.model, self.result)
                    self.mn_canvas.figure.tight_layout()
                    self.mn_canvas.draw()
                    plot_shear_view(self.nt_canvas.axes, input_name, self.model, self.result)
                    self.nt_canvas.figure.tight_layout()
                    self.nt_canvas.draw()
                    self.fill_results_table()
                    self.report_edit.setPlainText(format_model_report(self.model))
                    status = "optimalni" if self.result.success else self.result.message
                    self.status_label.setText(f"Stav: {status}, lambda = {self.result.load_factor:.6f}")
                except Exception as exc:  # noqa: BLE001
                    self.status_label.setText(f"Chyba: {exc}")
                    QMessageBox.critical(self, "Chyba vypoctu", f"{exc}\n\n{traceback.format_exc()}")

            def set_data(self, data: ArchLBTInput) -> None:
                self.data = data
                self.path_edit.setText(str(data.path))
                self.fields["span"].setValue(data.span)
                self.fields["rise"].setValue(data.rise)
                self.set_combo_value(self.geom_combo, data.geom_code)
                self.set_combo_value(self.extrados_combo, data.extrados_mode)
                self.fields["thickness"].setValue(data.thickness)
                self.fields["arch_width"].setValue(data.arch_width)
                self.fields["masonry_unit_weight"].setValue(data.masonry_unit_weight)
                self.fields["block_count"].setValue(data.block_count)
                self.fields["fill_height"].setValue(data.fill_height)
                self.fields["fill_unit_weight"].setValue(data.fill_unit_weight)
                self.set_combo_value(self.q_combo, data.q_code)
                self.fields["fill_spread_angle_deg"].setValue(data.fill_spread_angle * 180.0 / 3.1415926535)
                self.fields["friction_coefficient"].setValue(data.friction_coefficient)
                self.fields["compression_strength"].setValue(data.compression_strength)
                self.loads_table.setRowCount(0)
                for load in data.point_loads:
                    self.add_load_row(load)

            def collect_data(self, path: Path) -> ArchLBTInput:
                loads = []
                for row in range(self.loads_table.rowCount()):
                    values = []
                    for column in range(3):
                        item = self.loads_table.item(row, column)
                        values.append(float(item.text().replace(",", ".")) if item is not None and item.text().strip() else 0.0)
                    loads.append(PointLoad(values[0], values[1], values[2]))
                return ArchLBTInput(
                    path=Path(path),
                    span=self.fields["span"].value(),
                    rise=self.fields["rise"].value(),
                    geom_code=int(self.geom_combo.currentData()),
                    extrados_mode=str(self.extrados_combo.currentData()),
                    thickness=self.fields["thickness"].value(),
                    arch_width=self.fields["arch_width"].value(),
                    masonry_unit_weight=self.fields["masonry_unit_weight"].value(),
                    block_count=self.fields["block_count"].value(),
                    point_loads=tuple(loads),
                    fill_height=self.fields["fill_height"].value(),
                    fill_unit_weight=self.fields["fill_unit_weight"].value(),
                    q_code=int(self.q_combo.currentData()),
                    fill_spread_angle=self.fields["fill_spread_angle_deg"].value() * 3.1415926535 / 180.0,
                    friction_coefficient=self.fields["friction_coefficient"].value(),
                    compression_strength=self.fields["compression_strength"].value(),
                )

            def add_load_row(self, load: PointLoad | None = None) -> None:
                row = self.loads_table.rowCount()
                self.loads_table.insertRow(row)
                values = (0.0, 0.0, 0.0) if load is None else (load.x, load.force, load.width)
                for column, value in enumerate(values):
                    self.loads_table.setItem(row, column, QTableWidgetItem(f"{value:.12g}"))

            def remove_selected_loads(self) -> None:
                rows = sorted({item.row() for item in self.loads_table.selectedItems()}, reverse=True)
                for row in rows:
                    self.loads_table.removeRow(row)

            def fill_results_table(self) -> None:
                state = self.result.final_state
                intrados = self.model.intrados
                extrados = self.model.extrados
                self.result_table.setRowCount(len(state.normal_forces))
                for row, (normal, moment, shear) in enumerate(zip(state.normal_forces, state.moments, state.shear_forces)):
                    eccentricity = moment / normal if abs(normal) > 1e-12 else 0.0
                    values = [
                        row,
                        intrados[row, 0],
                        intrados[row, 1],
                        extrados[row, 0],
                        extrados[row, 1],
                        normal,
                        moment,
                        shear,
                        eccentricity,
                    ]
                    for column, value in enumerate(values):
                        text = str(value) if column == 0 else f"{value:.8g}"
                        item = QTableWidgetItem(text)
                        item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        self.result_table.setItem(row, column, item)
                self.result_table.resizeColumnsToContents()

            def copy_current_tab(self) -> None:
                widget = self.tabs.currentWidget()
                if widget is self.result_table:
                    QApplication.clipboard().setText(self.table_to_tsv(self.result_table))
                elif widget is self.report_edit:
                    selected = self.report_edit.textCursor().selectedText()
                    QApplication.clipboard().setText(selected.replace("\u2029", "\n") if selected else self.report_edit.toPlainText())
                elif widget is self.arch_canvas:
                    image = self.crop_vertical_whitespace(self.figure_to_array(self.arch_canvas.figure))
                    QApplication.clipboard().setPixmap(self.array_to_pixmap(image))
                elif widget in (self.mn_canvas, self.nt_canvas):
                    QApplication.clipboard().setPixmap(widget.grab())

            def export_pdf(self) -> None:
                if self.model is None or self.result is None:
                    self.solve_current()
                default_name = Path(self.data.path).with_suffix(".pdf").name if self.data.path else "arch_lbt_report.pdf"
                filename, _ = QFileDialog.getSaveFileName(self, "Export protokolu do PDF", default_name, "PDF files (*.pdf);;All files (*)")
                if not filename:
                    return
                try:
                    with PdfPages(filename) as pdf:
                        figure, axis, y = self.new_pdf_page("ArchLBT vypocetni protokol")
                        figure, axis, y = self.add_pdf_text_block(pdf, figure, axis, y, "1) Zadani ulohy", format_arch_lbt_input(self.data), font_size=7.5, width=108)
                        figure, axis, y = self.add_pdf_figure_block(pdf, figure, axis, y, "2) Obrazek Klenba", self.arch_canvas.figure, height=0.56, crop_vertical=True)
                        figure, axis, y = self.add_pdf_figure_block(pdf, figure, axis, y, "3) Graf M-N", self.mn_canvas.figure, height=0.35)
                        figure, axis, y = self.add_pdf_figure_block(pdf, figure, axis, y, "4) Graf N-T", self.nt_canvas.figure, height=0.35)
                        figure, axis, y = self.add_pdf_text_block(pdf, figure, axis, y, "5) Vysledky", self.aligned_table_text(self.result_table), font_size=6.2, width=132)
                        figure, axis, y = self.add_pdf_text_block(pdf, figure, axis, y, "6) Report", self.report_edit.toPlainText(), font_size=7.2, width=112)
                        figure, axis, y = self.add_generated_fields_blocks(pdf, figure, axis, y)
                        pdf.savefig(figure)
                    self.status_label.setText(f"PDF exportovano: {filename}")
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.critical(self, "Chyba exportu PDF", f"{exc}\n\n{traceback.format_exc()}")

            def add_generated_fields_blocks(self, pdf, figure, axis, y):
                fields = [
                    ("local coordinates", self.model.prepared.local_coordinates),
                    ("masonry loads", self.model.prepared.transformed_masonry),
                    ("backfill loads", self.model.prepared.transformed_fill),
                    ("variable loads", self.model.prepared.transformed_external),
                ]
                parts = []
                for name, values in fields:
                    parts.append(f"{name} = {values.shape[0]} x {values.shape[1]}")
                    parts.append(np.array2string(values, precision=8, suppress_small=False, max_line_width=132))
                    parts.append("")
                return self.add_pdf_text_block(pdf, figure, axis, y, "7) Generovana pole", "\n".join(parts), font_size=6.2, width=132)

            def new_pdf_page(self, title: str | None = None):
                figure = Figure(figsize=(8.27, 11.69), dpi=120)
                axis = figure.add_axes([0, 0, 1, 1])
                axis.axis("off")
                y = 0.965
                if title:
                    axis.text(0.05, y, title, ha="left", va="top", fontsize=13, weight="bold")
                    y -= 0.035
                return figure, axis, y

            def add_pdf_text_block(self, pdf, figure, axis, y, title: str, text: str, font_size: float = 7.5, width: int = 112):
                lines = self.wrap_pdf_lines(text, width=width)
                line_height = font_size * 0.00165
                title_height = 0.028
                first_page = True
                index = 0
                while index < len(lines):
                    available = y - 0.055 - title_height
                    if available < 0.12:
                        pdf.savefig(figure)
                        figure, axis, y = self.new_pdf_page()
                        available = y - 0.055 - title_height
                    line_count = max(1, int(available / line_height))
                    chunk = lines[index : index + line_count]
                    heading = title if first_page else f"{title} / pokracovani"
                    axis.text(0.05, y, heading, ha="left", va="top", fontsize=10, weight="bold")
                    y -= title_height
                    axis.text(0.05, y, "\n".join(chunk), ha="left", va="top", fontsize=font_size, family="monospace")
                    y -= line_height * len(chunk) + 0.018
                    index += len(chunk)
                    first_page = False
                return figure, axis, y

            def add_pdf_figure_block(self, pdf, figure, axis, y, title: str, source_figure, height: float = 0.28, crop_vertical: bool = False):
                needed = height + 0.045
                if y - needed < 0.055:
                    pdf.savefig(figure)
                    figure, axis, y = self.new_pdf_page()
                axis.text(0.05, y, title, ha="left", va="top", fontsize=10, weight="bold")
                y -= 0.026
                image = self.figure_to_array(source_figure)
                if crop_vertical:
                    image = self.crop_vertical_whitespace(image)
                image_axis = figure.add_axes([0.08, y - height, 0.84, height])
                image_axis.imshow(image)
                image_axis.axis("off")
                y -= height + 0.022
                return figure, axis, y

            def figure_to_array(self, figure):
                canvas = FigureCanvasAgg(figure)
                canvas.draw()
                return np.asarray(canvas.buffer_rgba())

            def crop_vertical_whitespace(self, image, threshold: int = 248, padding: int = 10):
                rgb = image[:, :, :3]
                alpha = image[:, :, 3]
                non_white = (np.any(rgb < threshold, axis=2)) & (alpha > 0)
                rows = np.flatnonzero(np.any(non_white, axis=1))
                if len(rows) == 0:
                    return image
                top = max(int(rows[0]) - padding, 0)
                bottom = min(int(rows[-1]) + padding + 1, image.shape[0])
                return image[top:bottom, :, :]

            def array_to_pixmap(self, image):
                contiguous = np.ascontiguousarray(image)
                height, width, channels = contiguous.shape
                bytes_per_line = channels * width
                qimage = QImage(contiguous.data, width, height, bytes_per_line, QImage.Format_RGBA8888).copy()
                return QPixmap.fromImage(qimage)

            def wrap_pdf_lines(self, text: str, width: int) -> list[str]:
                result = []
                for line in text.splitlines():
                    if len(line) <= width:
                        result.append(line)
                    else:
                        result.extend(textwrap.wrap(line, width=width, replace_whitespace=False, drop_whitespace=False) or [""])
                return result or [""]

            def table_to_tsv(self, table: QTableWidget) -> str:
                ranges = table.selectedRanges()
                if ranges:
                    selected = ranges[0]
                    top_row = selected.topRow()
                    bottom_row = selected.bottomRow()
                    left_column = selected.leftColumn()
                    right_column = selected.rightColumn()
                else:
                    top_row = 0
                    bottom_row = table.rowCount() - 1
                    left_column = 0
                    right_column = table.columnCount() - 1
                lines = []
                headers = []
                for column in range(left_column, right_column + 1):
                    header = table.horizontalHeaderItem(column)
                    headers.append("" if header is None else header.text())
                if headers:
                    lines.append("\t".join(headers))
                for row in range(top_row, bottom_row + 1):
                    cells = []
                    for column in range(left_column, right_column + 1):
                        item = table.item(row, column)
                        cells.append("" if item is None else item.text())
                    lines.append("\t".join(cells))
                return "\n".join(lines)

            def aligned_table_text(self, table: QTableWidget) -> str:
                rows = []
                headers = []
                for column in range(table.columnCount()):
                    header = table.horizontalHeaderItem(column)
                    headers.append("" if header is None else header.text())
                rows.append(headers)
                for row in range(table.rowCount()):
                    rows.append([
                        "" if table.item(row, column) is None else table.item(row, column).text()
                        for column in range(table.columnCount())
                    ])
                widths = [max(len(row[column]) for row in rows) for column in range(table.columnCount())]
                lines = []
                for row_index, row in enumerate(rows):
                    lines.append("  ".join(row[column].rjust(widths[column]) for column in range(table.columnCount())))
                    if row_index == 0:
                        lines.append("  ".join("-" * widths[column] for column in range(table.columnCount())))
                return "\n".join(lines)

            def set_combo_value(self, combo: QComboBox, value) -> None:
                index = combo.findData(value)
                combo.setCurrentIndex(max(index, 0))

        return _MainWindow()


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from algos import BrickByBrick, LimitedCourseStride
from bonds import FlemishBond, StretcherBond, WildBond
from wall import Wall

if TYPE_CHECKING:
    from algorithm import BuildAlgorithm

# Disclaimer: This GUI is mostly `vibe` coded and adjusted for usability.
# I had implemented a pure terminal interface first, but it was annoying me
# that the bricks could not be visualized correctly due to low resolution.


# --- Selection Dialog --- #
class WallSelectionDialog(QDialog):
    """Dialog to select wall dimensions, bond type, and algorithm"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wall Selection")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Wall dimensions
        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 5000)
        self.width_spin.setValue(2300)
        self.width_spin.setSingleStep(10)
        layout.addRow("Wall Width (mm):", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 4000)
        self.height_spin.setValue(2000)
        self.height_spin.setSingleStep(10)
        layout.addRow("Wall Height (mm):", self.height_spin)

        # Bond type
        self.bond_combo = QComboBox()
        self.bond_types = {
            "Stretcher Bond": StretcherBond,
            "Flemish Bond": FlemishBond,
            "Wild Bond": WildBond,
        }
        self.bond_combo.addItems(self.bond_types.keys())
        layout.addRow("Bond Type:", self.bond_combo)

        # Algorithm type
        self.algo_combo = QComboBox()
        self.algorithms = {
            "Limited Course Stride": LimitedCourseStride,
            "Brick By Brick": BrickByBrick,
        }
        self.algo_combo.addItems(self.algorithms.keys())
        layout.addRow("Algorithm:", self.algo_combo)

        # OK / Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_selection(self):
        """Return selected wall parameters"""
        width = self.width_spin.value()
        height = self.height_spin.value()
        bond_class = self.bond_types[self.bond_combo.currentText()]
        algo_class = self.algorithms[self.algo_combo.currentText()]
        return width, height, bond_class, algo_class


# --- Wall Canvas --- #
class WallCanvas(QWidget):
    """Custom widget for rendering the brick wall"""

    def __init__(self, wall: Wall, algorithm: BuildAlgorithm, parent=None):
        super().__init__(parent)
        self.wall = wall
        self.algorithm = algorithm
        self.setMinimumSize(800, 600)

        # Stride colors
        self.stride_colors = [
            QColor(255, 107, 107),
            QColor(78, 205, 196),
            QColor(69, 183, 209),
            QColor(255, 160, 122),
            QColor(152, 216, 200),
            QColor(247, 220, 111),
            QColor(187, 143, 206),
            QColor(133, 193, 226),
            QColor(248, 177, 149),
            QColor(192, 108, 132),
            QColor(108, 91, 123),
            QColor(53, 92, 125),
            QColor(20, 90, 50),
            QColor(105, 105, 105),
        ]

    def paintEvent(self, event):
        """Draw the wall"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        from config import BED_JOINT_HEIGHT, BRICK_HEIGHT

        brick_height_mm = BRICK_HEIGHT
        joint_height_mm = BED_JOINT_HEIGHT
        course_height_mm = brick_height_mm + joint_height_mm

        padding = 20
        available_width = self.width() - 2 * padding
        available_height = self.height() - 2 * padding

        scale_x = available_width / self.wall.width
        scale_y = available_height / self.wall.height
        scale = min(scale_x, scale_y)

        scaled_width = self.wall.width * scale
        scaled_height = self.wall.height * scale
        offset_x = (self.width() - scaled_width) / 2
        offset_y = (self.height() - scaled_height) / 2

        painter.fillRect(self.rect(), QColor(245, 245, 245))

        for course_idx, course in enumerate(self.wall.courses):
            y_bottom = course_idx * course_height_mm
            for brick in course:
                if brick.x_start is None or brick.x_end is None:
                    continue

                x1 = offset_x + brick.x_start * scale
                y1 = offset_y + (self.wall.height - y_bottom - brick_height_mm) * scale
                width = (brick.x_end - brick.x_start) * scale
                height = brick_height_mm * scale

                if brick.placed:
                    color = self.stride_colors[
                        brick.stride_index % len(self.stride_colors)
                    ]
                    pen = QPen(QColor(0, 0, 0), 1)
                else:
                    color = QColor(255, 255, 255)
                    pen = QPen(QColor(180, 180, 180), 1)

                painter.setPen(pen)
                painter.setBrush(QBrush(color))
                painter.drawRect(QRectF(x1, y1, width, height))

        # Draw border
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(offset_x, offset_y, scaled_width, scaled_height))

        # Draw the robot's stride (build envelope)
        if hasattr(self.algorithm, "build_envelope") and hasattr(
            self.algorithm, "current_stride_x_min"
        ):
            envelope_width, envelope_height = self.algorithm.build_envelope
            x_min = self.algorithm.current_stride_x_min
            y_min = self.algorithm.current_stride_y_min

            # Scale the envelope dimensions and position
            scaled_envelope_width = envelope_width * scale
            scaled_envelope_height = envelope_height * scale
            scaled_x_min = x_min * scale
            scaled_y_min = y_min * scale

            # Calculate the rectangle coordinates in canvas space
            rect_x = offset_x + scaled_x_min
            rect_y = offset_y + (scaled_height - scaled_y_min - scaled_envelope_height)

            # Draw the rectangle
            pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(
                QRectF(rect_x, rect_y, scaled_envelope_width, scaled_envelope_height)
            )


# --- Visualizer Window --- #
class WallVisualizerWindow(QMainWindow):
    def __init__(self, algorithm: BuildAlgorithm):
        super().__init__()
        self.algorithm = algorithm
        self.wall = algorithm.wall

        self.setWindowTitle(f"Brick Wall Builder - {self.wall.bond.name}")
        self.setGeometry(100, 100, 1400, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        info_text = f"Wall: {self.wall.width}mm x {self.wall.height}mm | Bond: {self.wall.bond.name}"
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 11pt; padding: 5px; font-style: italic;")
        main_layout.addWidget(info_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = WallCanvas(self.wall, self.algorithm)
        splitter.addWidget(self.canvas)

        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(10, 0, 10, 0)

        stats_title = QLabel("Statistics")
        stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_title.setStyleSheet("font-size: 12pt; font-weight: bold; padding: 5px;")
        stats_layout.addWidget(stats_title)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumWidth(300)
        self.stats_text.setMinimumWidth(250)
        self.stats_text.setFont(QFont("Courier", 9))
        stats_layout.addWidget(self.stats_text)

        splitter.addWidget(stats_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_one = QPushButton("Place 1 Brick")
        btn_one.clicked.connect(self.place_one)
        btn_ten = QPushButton("Place 10 Bricks")
        btn_ten.clicked.connect(self.place_ten)
        btn_stride = QPushButton("Complete Stride")
        btn_stride.clicked.connect(self.complete_stride)
        btn_finish = QPushButton("Finish Wall")
        btn_finish.clicked.connect(self.finish_wall)
        btn_quit = QPushButton("Quit")
        btn_quit.clicked.connect(self.close)

        for btn in [btn_one, btn_ten, btn_stride, btn_finish, btn_quit]:
            btn.setMinimumWidth(120)
            button_layout.addWidget(btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to build")

        # Button styles
        button_style = """
            QPushButton { padding: 8px 16px; font-size: 10pt; border-radius: 4px;
            background-color: #4A90E2; color: white; border: none; }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:pressed { background-color: #2868A8; }
        """
        quit_style = (
            button_style.replace("#4A90E2", "#E74C3C")
            .replace("#357ABD", "#C0392B")
            .replace("#2868A8", "#A93226")
        )
        for btn in [btn_one, btn_ten, btn_stride, btn_finish]:
            btn.setStyleSheet(button_style)
        btn_quit.setStyleSheet(quit_style)

        self.update_stats()

    # --- Stats / Brick Placement Methods --- #
    def update_stats(self):
        """Update the statistics display"""
        # Check if algorithm has statistics method
        if not hasattr(self.algorithm, "statistics"):
            self.stats_text.setPlainText(
                "Statistics not available\nfor this algorithm."
            )
            return

        stats = self.algorithm.statistics()

        if not stats:
            # Wall not complete yet - show partial stats
            total_bricks = sum(1 for course in self.wall.courses for brick in course)
            placed_bricks = sum(
                1 for course in self.wall.courses for brick in course if brick.placed
            )

            text = "═══ Build Progress ═══\n\n"
            text += f"Bricks Placed: {placed_bricks} / {total_bricks}\n"
            text += f"Progress: {(placed_bricks/total_bricks*100):.1f}%\n\n"

            # Add algorithm-specific info if available
            if hasattr(self.algorithm, "build_envelope"):
                text += "═══ Build Envelope ═══\n\n"
                text += f"Width:  {self.algorithm.build_envelope[0]} mm\n"
                text += f"Height: {self.algorithm.build_envelope[1]} mm\n\n"

            if hasattr(self.algorithm, "current_stride"):
                text += "═══ Current Status ═══\n\n"
                text += f"Stride: {self.algorithm.current_stride}\n"
                if hasattr(self.algorithm, "current_section"):
                    text += f"Section: {self.algorithm.current_section + 1}"
                    if hasattr(self.algorithm, "sections"):
                        text += f" / {self.algorithm.sections}"
                    text += "\n"
                if hasattr(self.algorithm, "platform_moves"):
                    text += f"Platform Moves: {self.algorithm.platform_moves}\n"
        else:
            # Wall complete - show full stats
            text = "═══ Build Complete! ═══\n\n"

            if hasattr(self.algorithm, "build_envelope"):
                text += "═══ Build Envelope ═══\n\n"
                text += f"Width:  {self.algorithm.build_envelope[0]} mm\n"
                text += f"Height: {self.algorithm.build_envelope[1]} mm\n\n"

            text += "═══ Wall Dimensions ═══\n\n"
            text += f"Width:  {self.wall.width} mm\n"
            text += f"Height: {self.wall.height} mm\n\n"

            text += "═══ Build Statistics ═══\n\n"

            if "total_robot_moves" in stats:
                text += f"Robot Moves: {stats['total_robot_moves']}\n"
            if "total_platform_moves" in stats:
                text += f"Platform Moves: {stats['total_platform_moves']}\n"
            if "average_bricks_per_stride" in stats:
                text += f"Avg Bricks/Stride: {stats['average_bricks_per_stride']:.2f}\n"
            text += f"\nTotal Bricks: {stats['total_bricks']}\n"
            if "total_brick_length" in stats:
                text += f"Total Length: {stats['total_brick_length']} mm\n"
            text += f"Total Courses: {stats['total_courses']}\n"

        self.stats_text.setPlainText(text)

    def place_one(self):
        if not self.algorithm.place_next_brick():
            self.check_wall_complete()
        else:
            self.canvas.update()
            self.update_stats()
            self.status_bar.showMessage("Placed 1 brick")

    def place_ten(self):
        placed = sum(self.algorithm.place_next_brick() for _ in range(10))
        if placed == 0:
            self.check_wall_complete()
        else:
            self.canvas.update()
            self.update_stats()
            self.status_bar.showMessage(f"Placed {placed} bricks")

    def complete_stride(self):
        try:
            count = self.algorithm.complete_stride()
            self.canvas.update()
            self.update_stats()
            self.status_bar.showMessage(f"Completed stride with {count} bricks")
            if count == 0:
                self.check_wall_complete()
        except NotImplementedError:
            self.status_bar.showMessage("Complete stride not implemented")

    def finish_wall(self):
        placed = 0
        while self.algorithm.next_brick() is not None:
            self.algorithm.place_next_brick()
            placed += 1
        self.canvas.update()
        self.update_stats()
        self.check_wall_complete(f"Wall complete! Placed {placed} bricks ")

    def check_wall_complete(self, message: str = "Wall complete! "):
        if self.wall.complete:
            self.status_bar.showMessage(message)
        else:
            self.status_bar.showMessage("No more bricks can be placed, stalled... ")


# --- Visualization Entry --- #
def visualize_wall(algorithm: BuildAlgorithm):
    app = QApplication.instance() or QApplication([])
    window = WallVisualizerWindow(algorithm)
    window.show()
    app.exec()


# --- Main Execution --- #
if __name__ == "__main__":
    app = QApplication([])

    # Show selection dialog first
    dialog = WallSelectionDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        width, height, bond_class, algo_class = dialog.get_selection()
        bond = bond_class()
        wall = Wall(width=width, height=height, bond=bond)
        if isinstance(bond, WildBond):
            bond.prepare_solution(wall)
        wall.generate_bond_design()
        wall.assign_support_relations()
        wall.validate_support_relations()

        algorithm = algo_class(wall)
        visualize_wall(algorithm)

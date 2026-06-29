import os
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import styles
from contestant_window import ContestantWindow
from csv_handler import CSVHandler, CSVHandlerError
from game_state import GameState
from presenter_window import PresenterWindow
from utils import get_app_dir


APP_DIR = get_app_dir()

COLOR_PALETTE = [
    {"name": "ブルー (青)", "hex": "#2563eb"},
    {"name": "グリーン (緑)", "hex": "#16a34a"},
    {"name": "ピンク", "hex": "#db2777"},
    {"name": "オレンジ", "hex": "#ea580c"},
    {"name": "レッド (赤)", "hex": "#dc2626"},
    {"name": "パープル (紫)", "hex": "#7c3aed"},
    {"name": "シアン (水色)", "hex": "#0891b2"},
    {"name": "イエロー (黄色)", "hex": "#ca8a04"},
]

SHUFFLE_OPTIONS = ["シャッフルなし", "シャッフルあり"]


class NumberStepper(QWidget):
    """Compact spin box with app-styled minus/plus buttons."""

    valueChanged = Signal(int)

    def __init__(self, minimum, maximum, value, parent=None):
        super().__init__(parent)
        self.setObjectName("number_stepper")

        self.spin = QSpinBox(self)
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin.setFixedWidth(52)
        self.spin.valueChanged.connect(self.valueChanged.emit)

        self.minus_btn = QPushButton("-", self)
        self.plus_btn = QPushButton("+", self)
        for button in (self.minus_btn, self.plus_btn):
            button.setObjectName("stepper_btn")
            button.setFixedSize(30, 30)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.minus_btn.clicked.connect(self.spin.stepDown)
        self.plus_btn.clicked.connect(self.spin.stepUp)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.minus_btn)
        layout.addWidget(self.spin)
        layout.addWidget(self.plus_btn)

        self.setStyleSheet(
            """
            QWidget#number_stepper {
                background: transparent;
            }
            QWidget#number_stepper QSpinBox {
                background-color: #0f172a;
                border: 1px solid #475569;
                border-radius: 6px;
                color: #f8fafc;
                font-size: 15px;
                font-weight: 700;
                padding: 4px 6px;
            }
            QWidget#number_stepper QPushButton#stepper_btn {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 17px;
                font-weight: 700;
                padding: 0;
            }
            QWidget#number_stepper QPushButton#stepper_btn:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #ffffff;
            }
            QWidget#number_stepper QPushButton#stepper_btn:pressed {
                background-color: #0f172a;
                border-color: #0ea5e9;
            }
            """
        )

    def value(self):
        return self.spin.value()

    def setValue(self, value):
        self.spin.setValue(value)

    def setRange(self, minimum, maximum):
        self.spin.setRange(minimum, maximum)


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)
            continue

        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


class SetupWindow(QDialog):
    """Setup and launcher dialog to configure game parameters or resume saved state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("クイズ用オセロ - 初期設定")
        self.setMinimumSize(500, 600)
        self.setStyleSheet(styles.APP_STYLE)
        self.game_state = None
        self.player_inputs = []

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("クイズ用オセロ 設定画面", self)
        header.setObjectName("title_header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        self.new_game_box = QGroupBox("新規ゲーム設定", self)
        self.new_game_layout = QVBoxLayout(self.new_game_box)
        self.new_game_layout.setSpacing(12)

        csv_row = QHBoxLayout()
        self.csv_path_input = QLineEdit(self)
        self.csv_path_input.setPlaceholderText("CSVファイルを選択してください...")
        self.csv_browse_btn = QPushButton("参照...", self)
        self.csv_browse_btn.clicked.connect(self.browse_csv)
        csv_row.addWidget(self.csv_path_input, 4)
        csv_row.addWidget(self.csv_browse_btn, 1)
        self.new_game_layout.addLayout(csv_row)

        dims_layout = QHBoxLayout()
        dims_layout.addWidget(QLabel("行数 (縦):", self))
        self.rows_spin = NumberStepper(3, 10, 5, self)
        dims_layout.addWidget(self.rows_spin)

        dims_layout.addWidget(QLabel("列数 (横):", self))
        self.cols_spin = NumberStepper(3, 10, 5, self)
        dims_layout.addWidget(self.cols_spin)
        self.new_game_layout.addLayout(dims_layout)

        shuffle_layout = QHBoxLayout()
        shuffle_layout.addWidget(QLabel("問題シャッフル設定:", self))
        self.shuffle_combo = QComboBox(self)
        self.shuffle_combo.addItems(SHUFFLE_OPTIONS)
        shuffle_layout.addWidget(self.shuffle_combo, 1)
        self.new_game_layout.addLayout(shuffle_layout)

        player_header = QHBoxLayout()
        player_header.addWidget(QLabel("プレイヤー人数:", self))
        self.player_count_spin = NumberStepper(2, 8, 3, self)
        self.player_count_spin.valueChanged.connect(self.update_player_inputs)
        player_header.addWidget(self.player_count_spin)
        self.new_game_layout.addLayout(player_header)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(180)
        self.scroll_area.setStyleSheet("background: transparent; border: 1px solid #475569; border-radius: 4px;")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_form = QFormLayout(self.scroll_content)
        self.scroll_form.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        self.new_game_layout.addWidget(self.scroll_area)
        layout.addWidget(self.new_game_box)

        self.resume_box = QGroupBox("保存データから再開", self)
        self.resume_layout = QVBoxLayout(self.resume_box)
        self.resume_btn = QPushButton("JSONファイルを選択してゲーム再開...", self)
        self.resume_btn.clicked.connect(self.resume_game_from_json)
        self.resume_layout.addWidget(self.resume_btn)
        layout.addWidget(self.resume_box)

        action_layout = QHBoxLayout()
        self.start_btn = QPushButton("ゲーム開始", self)
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.clicked.connect(self.start_new_game)
        self.exit_btn = QPushButton("閉じる", self)
        self.exit_btn.clicked.connect(self.reject)
        action_layout.addWidget(self.exit_btn, 1)
        action_layout.addWidget(self.start_btn, 2)
        layout.addLayout(action_layout)

        default_csv = os.path.join(APP_DIR, "quiz_sample.csv")
        if os.path.exists(default_csv):
            self.csv_path_input.setText(default_csv)

        self.update_player_inputs()

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "クイズCSVを選択", APP_DIR, "CSV Files (*.csv)")
        if file_path:
            self.csv_path_input.setText(file_path)

    def update_player_inputs(self):
        previous_players = [
            (name_widget.text(), color_widget.currentData())
            for name_widget, color_widget in self.player_inputs
        ]

        clear_layout(self.scroll_form)
        self.player_inputs.clear()

        for i in range(self.player_count_spin.value()):
            row_layout = QHBoxLayout()

            name_input = QLineEdit(self)
            name_input.setPlaceholderText(f"プレイヤー {i + 1} の名前")
            if i < len(previous_players):
                name_input.setText(previous_players[i][0])

            color_combo = QComboBox(self)
            for color_data in COLOR_PALETTE:
                color_combo.addItem(color_data["name"], color_data["hex"])
            if i < len(previous_players):
                previous_color = previous_players[i][1]
                previous_index = color_combo.findData(previous_color)
                color_combo.setCurrentIndex(previous_index if previous_index >= 0 else i % len(COLOR_PALETTE))
            else:
                color_combo.setCurrentIndex(i % len(COLOR_PALETTE))
            color_combo.setStyleSheet("QComboBox { padding-right: 20px; }")
            color_combo.currentIndexChanged.connect(
                lambda _index, name=name_input, combo=color_combo: self.apply_player_name_color(name, combo.currentData())
            )
            self.apply_player_name_color(name_input, color_combo.currentData())

            row_layout.addWidget(name_input, 2)
            row_layout.addWidget(color_combo, 1)

            self.scroll_form.addRow(QLabel(f"プレイヤー {i + 1}:"), row_layout)
            self.player_inputs.append((name_input, color_combo))

    def apply_player_name_color(self, name_input: QLineEdit, color: str):
        name_input.setStyleSheet(
            f"""
            QLineEdit {{
                color: {color};
                border-color: {color};
                font-weight: 700;
            }}
            """
        )

    def start_new_game(self):
        csv_path = self.csv_path_input.text().strip()
        if not csv_path:
            QMessageBox.critical(self, "エラー", "CSVファイルを選択してください。")
            return

        players = []
        selected_colors = set()

        for i, (name_widget, color_widget) in enumerate(self.player_inputs):
            name = name_widget.text().strip()
            color = color_widget.currentData()

            if not name:
                QMessageBox.critical(self, "エラー", f"プレイヤー {i + 1} の名前が空欄です。")
                return

            if color in selected_colors:
                QMessageBox.critical(self, "エラー", "重複した色が選ばれています。\nプレイヤー間で異なる色を選択してください。")
                return

            selected_colors.add(color)
            players.append({"name": name, "color": color})

        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        shuffle_type = self.shuffle_combo.currentText()

        try:
            questions, used_csv_path = CSVHandler.load_and_process_csv(csv_path, rows, cols, shuffle_type)
        except CSVHandlerError as exc:
            QMessageBox.critical(self, "CSVエラー", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "エラー", f"CSVの処理中に予期しないエラーが発生しました:\n{exc}")
            return

        self.game_state = GameState(
            rows=rows,
            cols=cols,
            csv_path=used_csv_path,
            original_csv_path=csv_path,
            shuffle_type=shuffle_type,
            questions=questions,
            players=players,
        )
        self.accept()

    def resume_game_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "セーブデータを選択", APP_DIR, "JSON Files (*.json)")
        if not file_path:
            return

        try:
            self.game_state = GameState.load_from_json_file(file_path)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "読み込みエラー", f"セーブデータのロードに失敗しました:\n{exc}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    setup = SetupWindow()
    if setup.exec() != QDialog.DialogCode.Accepted or not setup.game_state:
        sys.exit(0)

    state = setup.game_state
    presenter_win = PresenterWindow(state)
    contestant_win = ContestantWindow(state)
    presenter_win.contestant_window = contestant_win
    presenter_win.state_updated.connect(contestant_win.update_ui)

    contestant_win.show()
    presenter_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

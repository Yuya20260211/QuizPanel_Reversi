from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QLabel, QSizePolicy
import styles


class OthelloCellButton(QPushButton):
    """Shared Othello grid cell button used by both presenter and contestant windows."""

    def __init__(self, cell_id: int, genre: str, parent=None):
        super().__init__(parent)
        self.cell_id = cell_id
        self.genre = genre
        self.owner_color = None
        self.is_active = False
        self.genre_hidden = False
        self.setObjectName("othello_cell_button")
        self.setText("")
        self.setMinimumSize(72, 56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFlat(True)

        self.id_label = QLabel(str(cell_id), self)
        self.id_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.id_label.setStyleSheet(
            "background: transparent; color: rgba(255, 255, 255, 0.82);"
            " font-weight: bold; border: none; font-family: Arial;"
        )

        self.genre_label = QLabel(genre, self)
        self.genre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.genre_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.genre_label.setWordWrap(True)
        self.genre_label.setStyleSheet(
            "background: transparent; color: #ffffff; font-weight: bold;"
            " border: none; font-family: 'Yu Gothic UI', Meiryo, sans-serif;"
        )

        self.update_style()

    def set_owner(self, color: str | None):
        self.owner_color = color
        self.update_style(False)

    def set_active(self, active: bool):
        self.is_active = active
        self.update_style(False)

    def set_display(self, cell_id: int, genre: str):
        self.cell_id = cell_id
        self.genre = genre
        self.id_label.setText(str(cell_id))
        self.genre_label.setText(genre)
        self.layout_labels()

    def set_genre_hidden(self, hidden: bool):
        self.genre_hidden = hidden
        self.genre_label.setVisible(not hidden)
        self.layout_labels()

    def update_style(self, is_hovered: bool = False):
        if self.is_active:
            style_qss = (
                "background-color: #1e1b4b;"
                "border: 4px solid #facc15;"
                "border-radius: 8px;"
                "padding: 0px; margin: 0px;"
            )
        else:
            style_qss = styles.get_cell_style_qss(self.owner_color, is_hovered)
        self.setStyleSheet(style_qss)
        self.id_label.raise_()
        self.genre_label.raise_()

    def layout_labels(self):
        if self.genre_hidden:
            self.id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.id_label.setGeometry(6, 6, self.width() - 12, self.height() - 12)
        else:
            self.id_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.id_label.setGeometry(6, 4, self.width() - 12, 16)
            self.genre_label.setGeometry(6, 18, self.width() - 12, self.height() - 22)
        self.id_label.raise_()
        self.genre_label.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_labels()

    def enterEvent(self, event):
        self.update_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update_style(False)
        super().leaveEvent(event)

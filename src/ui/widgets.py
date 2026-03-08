"""Reusable UI widgets for the application."""

from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QTextFormat
from PyQt6.QtWidgets import QFrame, QPlainTextEdit, QLabel, QTextEdit, QVBoxLayout, QWidget


class StatCard(QFrame):
    def __init__(self, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self.setProperty("accent", accent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")

        self.value_label = QLabel("0")
        self.value_label.setObjectName("CardValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self.code_editor = editor
        self.setObjectName("LineNumberArea")

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("0") * digits + 8

    def update_line_number_area_width(self, _=0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        self.line_number_area.update()

    def update_line_number_area(self, rect, dy: int) -> None:
        if rect is None:
            self.line_number_area.update()
            return

        if not isinstance(rect, QRect):
            self.line_number_area.update()
            return

        safe_rect = rect
        viewport = self.viewport()
        if viewport is None:
            self.line_number_area.update()
            return
        viewport_rect = viewport.rect()

        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0,
                safe_rect.y(),
                self.line_number_area_width(),
                safe_rect.height(),
            )
        if safe_rect.contains(viewport_rect):
            self.update_line_number_area_width()

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#0d0d0d"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                line = str(block_number + 1)
                if block_number == self.textCursor().blockNumber():
                    painter.fillRect(
                        0,
                        top,
                        self.line_number_area.width(),
                        self.fontMetrics().height(),
                        QColor("#2a2a2a"),
                    )
                    painter.setPen(QColor("#d4d4d4"))
                else:
                    painter.setPen(QColor("#7f7f7f"))

                if bottom >= event.rect().top():
                    painter.drawText(
                        0,
                        top,
                        self.line_number_area.width() - 6,
                        self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                        line,
                    )

            block = block.next()
            block_number += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self) -> None:
        extra_selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#0b1f32"))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

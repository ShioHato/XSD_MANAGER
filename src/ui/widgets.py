"""Reusable UI widgets for the application."""

from PyQt6.QtCore import Qt, QRect, QSize, QRegularExpression
from PyQt6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextFormat, QSyntaxHighlighter
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


class XmlSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self) -> None:
        self.tag_name_format = QTextCharFormat()
        self.tag_name_format.setForeground(QColor("#569cd6"))
        self.tag_name_format.setFontWeight(QFont.Weight.Bold)

        self.attribute_name_format = QTextCharFormat()
        self.attribute_name_format.setForeground(QColor("#9cdcfe"))

        self.attribute_value_format = QTextCharFormat()
        self.attribute_value_format.setForeground(QColor("#ce9178"))

        self.attribute_equal_format = QTextCharFormat()
        self.attribute_equal_format.setForeground(QColor("#f0f0f0"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#608b4e"))

        self.pi_format = QTextCharFormat()
        self.pi_format.setForeground(QColor("#d7ba7d"))

    def _setup_rules(self) -> None:
        self.rules = [
            (QRegularExpression(r"<!--[\s\S]*?-->"), self.comment_format),
            (QRegularExpression(r"<\?[\s\S]*?\?>"), self.pi_format),
            (QRegularExpression(r"\b([A-Za-z_:][A-Za-z0-9._:-]*)\b(?=\s*=\")"), self.attribute_name_format),
            (QRegularExpression(r"\b([A-Za-z_:][A-Za-z0-9._:-]*)\b(?=\s*=')"), self.attribute_name_format),
            (QRegularExpression(r"([\"']).*?\1"), self.attribute_value_format),
            (QRegularExpression(r"</?[A-Za-z_:][A-Za-z0-9._:-]*"), self.tag_name_format),
        ]

    def highlightBlock(self, text: str) -> None:  # type: ignore[override]
        for expression, color_format in self.rules:
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), color_format)

        # Highlight equal signs between attribute names and values
        equal_expression = QRegularExpression(r"=")
        it_equal = equal_expression.globalMatch(text)
        while it_equal.hasNext():
            match = it_equal.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.attribute_equal_format)


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
        self.syntax_highlighter: XmlSyntaxHighlighter | None = None

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def set_syntax(self, enabled: bool) -> None:
        if enabled:
            if self.syntax_highlighter is None:
                self.syntax_highlighter = XmlSyntaxHighlighter(self.document())
        else:
            if self.syntax_highlighter is not None:
                self.syntax_highlighter.setDocument(None)
            self.syntax_highlighter = None

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

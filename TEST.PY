# NukeCodeBridge v0.11
# Network-Based Script Manager & Python Editor for Foundry Nuke

from __future__ import print_function

import re
import os
import sys
import traceback
import datetime
import __main__
import shutil


try:
    import nuke
except ImportError:
    nuke = None

# Try PySide2 first, then PySide6
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

BASE_SHARED_PATH = r"Y:\dev_remco\SharedNukeScripts"
SHOW_RUN_CONFIRMATION = True
USE_SINGLE_SHARED_FOLDER = False

ENABLE_BACKUPS = True
MAX_BACKUPS = 3
MAX_HISTORY_ITEMS = 25

# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_user_name():
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown_user"

def timestamp_string():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# ----------------------------------------------------------------------
# Stream Redirector (thread-safe)
# ----------------------------------------------------------------------

class StreamRedirector(QtCore.QObject):
    message_emitted = QtCore.Signal(str)

    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget
        self._old_stdout = None
        self._old_stderr = None
        self.message_emitted.connect(self.console_widget.appendPlainText)

    def write(self, text):
        if text:
            self.message_emitted.emit(text.rstrip("\n"))

    def flush(self):
        pass

    def __enter__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, *args):
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr

# ----------------------------------------------------------------------
# Line Number Area
# ----------------------------------------------------------------------

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)

# ----------------------------------------------------------------------
# Code Editor with Line Numbers, Highlight, Zoom, Indentation
# ----------------------------------------------------------------------

class CodeEditor(QtWidgets.QPlainTextEdit):
    zoomChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        # Font
        font = QtGui.QFont("Consolas", 10)
        self.setFont(font)
        self._default_point_size = font.pointSize()
        self._current_zoom = 0
        # VS Code Dark+ editor colors
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;      /* VS Code Dark+ background */
                color: #D4D4D4;                 /* VS Code default text */
                selection-background-color: #264F78;  /* VS Code selection blue */
            }
        """)


        # Tabs
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)

        # Line number area
        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.highlightOccurrences)

        self.updateLineNumberAreaWidth(0)

        # Current line highlight color
        self._current_line_color = QtGui.QColor(60, 60, 60, 80)

    # ------------------------------------------------------------
    # Line Numbers
    # ------------------------------------------------------------
    def lineNumberAreaWidth(self):
        digits = 1
        max_block = max(1, self.blockCount())
        while max_block >= 10:
            max_block //= 10
            digits += 1
        return 3 + self.fontMetrics().horizontalAdvance("9") * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor(40, 40, 40))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QtGui.QColor(160, 160, 160))
                painter.drawText(
                    0, top, self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                    number
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ------------------------------------------------------------
    # Highlight Current Line
    # ------------------------------------------------------------
    def highlightCurrentLine(self):
        extra = []
        if not self.isReadOnly():
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format.setBackground(self._current_line_color)
            sel.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    # ------------------------------------------------------------
    # Highlight All Occurrences of Selected Word
    # ------------------------------------------------------------
    def highlightOccurrences(self):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()

        # Only highlight valid identifiers
        if not word or not word.isidentifier():
            self.setExtraSelections(self.extraSelections()[:1])
            return

        doc = self.document()
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(QtGui.QColor(80, 80, 120, 120))

        selections = self.extraSelections()[:1]

        find_cursor = QtGui.QTextCursor(doc)
        while True:
            find_cursor = doc.find(word, find_cursor)
            if find_cursor.isNull():
                break

            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.cursor = find_cursor
            sel.format = fmt
            selections.append(sel)

        self.setExtraSelections(selections)

    # ------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------
    def wheelEvent(self, event):
        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoomIn(1)
            else:
                self.zoomOut(1)
            event.accept()
            return
        super().wheelEvent(event)

    def zoomIn(self, steps=1):
        super().zoomIn(steps)
        self._current_zoom += steps
        self.zoomChanged.emit(self._current_zoom)

    def zoomOut(self, steps=1):
        super().zoomOut(steps)
        self._current_zoom -= steps
        self.zoomChanged.emit(self._current_zoom)

    def reset_zoom(self):
        super().zoomOut(self._current_zoom)
        self._current_zoom = 0
        self.zoomChanged.emit(0)

    # ------------------------------------------------------------
    # Key Handling (Indent / Unindent)
    # ------------------------------------------------------------
    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        # Zoom shortcuts
        if mods & QtCore.Qt.ControlModifier:
            if key in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                self.zoomIn(1)
                return
            elif key == QtCore.Qt.Key_Minus:
                self.zoomOut(1)
                return
            elif key == QtCore.Qt.Key_0:
                self.reset_zoom()
                return

        # Indent
        if key == QtCore.Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._indent_selection(cursor)
            else:
                self.insertPlainText(" " * 4)
            return

        # Unindent
        if key == QtCore.Qt.Key_Backtab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._unindent_selection(cursor)
            else:
                self._unindent_current_line(cursor)
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------
    # Indent Helpers
    # ------------------------------------------------------------
    def _indent_selection(self, cursor):
        doc = self.document()
        start = doc.findBlock(cursor.selectionStart())
        end = doc.findBlock(cursor.selectionEnd() - 1)

        cursor.beginEditBlock()
        block = start
        while block.isValid():
            tc = QtGui.QTextCursor(block)
            tc.movePosition(QtGui.QTextCursor.StartOfBlock)
            tc.insertText(" " * 4)
            if block == end:
                break
            block = block.next()
        cursor.endEditBlock()

    def _unindent_selection(self, cursor):
        doc = self.document()
        start = doc.findBlock(cursor.selectionStart())
        end = doc.findBlock(cursor.selectionEnd() - 1)

        cursor.beginEditBlock()
        block = start
        while block.isValid():
            self._unindent_block(block)
            if block == end:
                break
            block = block.next()
        cursor.endEditBlock()

    def _unindent_current_line(self, cursor):
        cursor.beginEditBlock()
        self._unindent_block(cursor.block())
        cursor.endEditBlock()

    def _unindent_block(self, block):
        text = block.text()
        if not text:
            return

        remove = 0
        for ch in text:
            if ch in (" ", "\t") and remove < 4:
                remove += 1
            else:
                break

        if remove == 0:
            return

        tc = QtGui.QTextCursor(block)
        tc.movePosition(QtGui.QTextCursor.StartOfBlock)
        for _ in range(remove):
            tc.deleteChar()

    # Zoom helpers
    def zoomIn(self, steps=1):
        super().zoomIn(steps)
        self._current_zoom += steps
        self.zoomChanged.emit(self._current_zoom)

    def zoomOut(self, steps=1):
        super().zoomOut(steps)
        self._current_zoom -= steps
        self.zoomChanged.emit(self._current_zoom)

    def reset_zoom(self):
        super().zoomOut(self._current_zoom)
        self._current_zoom = 0
        self.zoomChanged.emit(0)

class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """VS Code Dark+ style Python syntax highlighting."""
    def __init__(self, document):
        super(PythonHighlighter, self).__init__(document)

        self.rules = []

        # ------------------------------------------------------------
        # VS CODE DARK+ COLORS (tuned for your background)
        # ------------------------------------------------------------
        COLOR_KEYWORD   = QtGui.QColor("#C586C0")   # purple
        COLOR_STRING    = QtGui.QColor("#CE9178")   # orange-ish string
        COLOR_COMMENT   = QtGui.QColor("#6A9955")   # green
        COLOR_CLASS     = QtGui.QColor("#4EC9B0")   # teal
        COLOR_FUNC      = QtGui.QColor("#DCDCAA")   # yellow
        COLOR_BUILTIN   = QtGui.QColor("#9CDCFE")   # light blue
        COLOR_NUM       = QtGui.QColor("#B5CEA8")   # soft green
        COLOR_DECORATOR = QtGui.QColor("#C8C8C8")   # light grey
        COLOR_OPERATOR  = QtGui.QColor("#D4D4D4")   # VS Code operator color

        # ------------------------------------------------------------
        # KEYWORDS (purple)
        # ------------------------------------------------------------
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(COLOR_KEYWORD)
        keywords = [
            "def", "class", "import", "from", "return", "if", "elif", "else",
            "try", "except", "finally", "for", "while", "in", "and", "or",
            "not", "pass", "break", "continue", "with", "as", "lambda",
            "yield", "assert", "del", "global", "nonlocal", "raise", "is"
        ]
        for kw in keywords:
            self.rules.append((rf"\\b{kw}\\b", keyword_format))

        # ------------------------------------------------------------
        # BUILTINS (light blue)
        # ------------------------------------------------------------
        builtin_format = QtGui.QTextCharFormat()
        builtin_format.setForeground(COLOR_BUILTIN)
        builtins = [
            "print", "len", "range", "dict", "list", "set", "tuple", "int",
            "float", "str", "bool", "type", "dir", "help", "isinstance",
            "issubclass", "open", "super", "enumerate", "zip", "map", "filter",
            "sum", "min", "max", "abs"
        ]
        for b in builtins:
            self.rules.append((rf"\\b{b}\\b", builtin_format))

        # ------------------------------------------------------------
        # STRINGS (orange)
        # ------------------------------------------------------------
        string_format = QtGui.QTextCharFormat()
        string_format.setForeground(COLOR_STRING)
        self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        self.rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))

        # ------------------------------------------------------------
        # COMMENTS (green)
        # ------------------------------------------------------------
        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(COLOR_COMMENT)
        self.rules.append((r"#.*", comment_format))

        # ------------------------------------------------------------
        # DECORATORS (@something)
        # ------------------------------------------------------------
        decorator_format = QtGui.QTextCharFormat()
        decorator_format.setForeground(COLOR_DECORATOR)
        self.rules.append((r"@\\w+", decorator_format))

        # ------------------------------------------------------------
        # CLASS NAMES (teal)
        # ------------------------------------------------------------
        class_format = QtGui.QTextCharFormat()
        class_format.setForeground(COLOR_CLASS)
        class_format.setFontWeight(QtGui.QFont.Bold)
        self.rules.append((r"\\bclass\\s+(\\w+)", class_format))

        # ------------------------------------------------------------
        # FUNCTION NAMES (yellow)
        # ------------------------------------------------------------
        func_format = QtGui.QTextCharFormat()
        func_format.setForeground(COLOR_FUNC)
        self.rules.append((r"\\bdef\\s+(\\w+)", func_format))

        # ------------------------------------------------------------
        # NUMBERS (soft green)
        # ------------------------------------------------------------
        num_format = QtGui.QTextCharFormat()
        num_format.setForeground(COLOR_NUM)
        self.rules.append((r"\\b[0-9]+\\b", num_format))

        # ------------------------------------------------------------
        # OPERATORS (VS Code grey)
        # ------------------------------------------------------------
        operator_format = QtGui.QTextCharFormat()
        operator_format.setForeground(COLOR_OPERATOR)
        operators = r"[+\-*/%=<>!]+"
        self.rules.append((operators, operator_format))

    # ------------------------------------------------------------
    # APPLY RULES
    # ------------------------------------------------------------
    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

    

# ----------------------------------------------------------------------
# Main UI
# ----------------------------------------------------------------------

class NukeCodeBridge(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(NukeCodeBridge, self).__init__(parent)
        self.setWindowTitle("NukeCodeBridge v0.11")
        self.exec_namespace = {}

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.raise_()
        self.activateWindow()

        self.current_user = get_user_name()
        self.current_repo_path = None
        self.global_zoom = 0

        self._init_paths()
        self._init_state()
        self._init_ui()
        self._refresh_script_list()
        self._update_status_bar()

    def _force_raise(self):
        QtCore.QTimer.singleShot(120, self.raise_)
        QtCore.QTimer.singleShot(120, self.activateWindow)

    def _exec_in_namespace(self, code):
        exec(code, self.exec_namespace)

    # -----------------------------
    # Init
    # -----------------------------
    def _init_paths(self):
        if USE_SINGLE_SHARED_FOLDER:
            self.current_repo_path = BASE_SHARED_PATH
        else:
            self.current_repo_path = os.path.join(BASE_SHARED_PATH, self.current_user)
        ensure_directory(self.current_repo_path)

    def _init_state(self):
        self.history_items = []
        self.max_history = MAX_HISTORY_ITEMS

    def _create_editor(self, content="", file_path=None):
        editor = CodeEditor()
        editor.setPlainText(content)
        editor.file_path = file_path

        # attach syntax highlighter
        PythonHighlighter(editor.document())

        # connect variable occurrence highlighting
        editor.cursorPositionChanged.connect(editor.highlightOccurrences)

        # apply global zoom
        if self.global_zoom != 0:
            if self.global_zoom > 0:
                editor.zoomIn(self.global_zoom)
            else:
                editor.zoomOut(-self.global_zoom)

        editor.textChanged.connect(self._on_editor_modified)
        editor.zoomChanged.connect(self._on_editor_zoom_changed)
        return editor

    # -----------------------------
    # Tabs & Editors
    # -----------------------------
    def _new_tab(self, title, content="", file_path=None):
        editor = self._create_editor(content, file_path)
        idx = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(idx)

    def _close_tab(self, index):
        if self.tab_widget.count() == 1:
            editor = self.tab_widget.widget(index)
            editor.setPlainText("")
            editor.file_path = None
            self.tab_widget.setTabText(index, "Untitled")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()

    def get_current_editor(self):
        return self.tab_widget.currentWidget()

    # -----------------------------
    # UI 
    # -----------------------------

    def _init_ui(self):
        # Main vertical layout for the whole window
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # 1. Script Name bar (Top)
        name_bar_layout = QtWidgets.QHBoxLayout()
        name_bar_layout.addWidget(QtWidgets.QLabel("Active Script Name:"))
        self.filename_edit = QtWidgets.QLineEdit()
        self.filename_edit.setPlaceholderText("Enter script_name.py here...")
        name_bar_layout.addWidget(self.filename_edit)
        main_layout.addLayout(name_bar_layout)

        # 2. Main Horizontal Splitter (Sidebar vs Editor Area)
        self.main_horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_layout.addWidget(self.main_horizontal_splitter, 1)

        # --- Left Panel (Sidebar) ---
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # User selection
        user_layout = QtWidgets.QHBoxLayout()
        self.user_combo = QtWidgets.QComboBox()

        users = []
        try:
            if os.path.exists(BASE_SHARED_PATH):
                for name in os.listdir(BASE_SHARED_PATH):
                    if os.path.isdir(os.path.join(BASE_SHARED_PATH, name)):
                        users.append(name)
        except:
            pass
        if self.current_user not in users:
            users.insert(0, self.current_user)
        if "all_users" not in users:
            users.append("all_users")

        self.user_combo.addItems(users)
        self.user_combo.setCurrentText(self.current_user)
        self.user_combo.currentTextChanged.connect(self._on_user_changed)
        user_layout.addWidget(QtWidgets.QLabel("Select User:"))
        user_layout.addWidget(self.user_combo)
        left_layout.addLayout(user_layout)

        # Search
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self._refresh_script_list)
        left_layout.addWidget(self.search_edit)

        # Script List
        self.script_list = QtWidgets.QListWidget()
        self.script_list.itemDoubleClicked.connect(self._on_script_double_clicked)
        self.script_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self._on_script_context_menu)
        left_layout.addWidget(self.script_list, 2)

        self.new_script_btn = QtWidgets.QPushButton("New Script")
        self.new_script_btn.clicked.connect(self._new_script)
        left_layout.addWidget(self.new_script_btn)

        # Execution History Group
        self.history_group = QtWidgets.QGroupBox("Execution History")
        history_layout = QtWidgets.QVBoxLayout(self.history_group)
        self.history_list = QtWidgets.QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_double_clicked)
        history_layout.addWidget(self.history_list)
        left_layout.addWidget(self.history_group, 1)

        # Variables Group
        self.vars_group = QtWidgets.QGroupBox("Session Variables")
        vars_layout = QtWidgets.QVBoxLayout(self.vars_group)
        self.vars_list = QtWidgets.QListWidget()
        vars_layout.addWidget(self.vars_list)
        left_layout.addWidget(self.vars_group, 1)

        # Manual Button
        self.help_btn = QtWidgets.QPushButton("⌨ Shortcuts & Manual")
        self.help_btn.setMinimumHeight(30)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                border: 1px solid #444444;
                color: #9CDCFE;
                font-weight: bold;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #444444;
                border: 1px solid #007ACC;
            }
        """)
        self.help_btn.clicked.connect(self._show_help_tab)
        left_layout.addWidget(self.help_btn)

        self.main_horizontal_splitter.addWidget(left_widget)

        # --- Right Panel (Editor + Console) ---
        right_main_container = QtWidgets.QWidget()
        right_main_layout = QtWidgets.QVBoxLayout(right_main_container)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(0)

        # Vertical Splitter (Editor vs Console)
        self.right_vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # Editor Tabs
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.right_vertical_splitter.addWidget(self.tab_widget)

        # --- Console Area ---
        console_container = QtWidgets.QWidget()
        console_v_layout = QtWidgets.QVBoxLayout(console_container)
        console_v_layout.setContentsMargins(0, 2, 0, 0)

        console_header = QtWidgets.QHBoxLayout()

        # Status Light
        self.status_light = QtWidgets.QLabel("●")
        self.status_light.setStyleSheet("color: #555; font-size: 18px; margin-right: 5px;")
        console_header.addWidget(self.status_light)

        console_header.addWidget(QtWidgets.QLabel("Console Output:"))
        console_header.addStretch()

        # Filter Mode Dropdown
        console_header.addWidget(QtWidgets.QLabel("View:"))
        self.console_mode = QtWidgets.QComboBox()
        self.console_mode.addItems(["All", "Errors Only", "Actions/Info"])
        self.console_mode.setFixedWidth(120)
        self.console_mode.currentIndexChanged.connect(self._apply_console_filter)
        console_header.addWidget(self.console_mode)

        console_v_layout.addLayout(console_header)

        self.console_output = QtWidgets.QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #1A1A1A; color: #D4D4D4;")
        self.console_output.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        console_v_layout.addWidget(self.console_output)

        self.right_vertical_splitter.addWidget(console_container)

        # Splitter scaling
        self.right_vertical_splitter.setStretchFactor(0, 4)
        self.right_vertical_splitter.setStretchFactor(1, 1)
        self.right_vertical_splitter.setCollapsible(0, False)
        self.right_vertical_splitter.setCollapsible(1, False)

        right_main_layout.addWidget(self.right_vertical_splitter, 1)

        # ------------------------------------------------------------
        # Bottom Button Row
        # ------------------------------------------------------------
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(4, 6, 4, 4)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.save_script)
        self.save_as_btn = QtWidgets.QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.save_script_as)
        self.run_btn = QtWidgets.QPushButton("Run Code")
        self.run_btn.clicked.connect(self.execute_code)
        self.run_sel_btn = QtWidgets.QPushButton("Run Selection")
        self.run_sel_btn.clicked.connect(self.execute_selection)
        self.refresh_vars_btn = QtWidgets.QPushButton("Refresh Vars")
        self.refresh_vars_btn.clicked.connect(self.refresh_variables)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.save_as_btn)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.run_sel_btn)
        btn_layout.addWidget(self.refresh_vars_btn)

        # ------------------------------------------------------------
        # Create Refresh Console Menu FIRST
        # ------------------------------------------------------------
        self.refresh_console_menu = QtWidgets.QMenu(self)
        soft_action = self.refresh_console_menu.addAction("Soft Refresh (keep errors/actions)")
        hard_action = self.refresh_console_menu.addAction("Hard Refresh (clear console)")
        reset_action = self.refresh_console_menu.addAction("Full Reset (console + filters)")

        soft_action.triggered.connect(self._console_soft_refresh)
        hard_action.triggered.connect(self._console_hard_refresh)
        reset_action.triggered.connect(self._console_full_reset)

        # ------------------------------------------------------------
        # Create Refresh Console Button SECOND
        # ------------------------------------------------------------
        self.refresh_console_btn = QtWidgets.QPushButton("Refresh Console")
        self.refresh_console_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D30;
                color: #9CDCFE;
                border: 1px solid #3C3C3C;
                padding: 4px 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
        """)
        self.refresh_console_btn.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.refresh_console_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
        self.refresh_console_btn.setMenu(self.refresh_console_menu)

        btn_layout.addWidget(self.refresh_console_btn)
        btn_layout.addStretch(1)

        right_main_layout.addLayout(btn_layout)

        # Final splitter setup
        self.main_horizontal_splitter.addWidget(right_main_container)
        self.main_horizontal_splitter.setStretchFactor(1, 1)

        # Status Bar (Bottom)
        self.status_bar = QtWidgets.QLabel()
        self.status_bar.setStyleSheet("font-size: 10px; color: #888; border-top: 1px solid #333;")
        main_layout.addWidget(self.status_bar)

        # Shortcuts
        self.save_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_script)

        self.run_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.run_shortcut.activated.connect(self.execute_code)

        self._new_tab("Untitled")

    def _console_soft_refresh(self):
        doc = self.console_output.document()
        new_lines = []
        block = doc.firstBlock()
        while block.isValid():
            state = block.userState()
            if state in (1, 2):
                new_lines.append((block.text(), state))
            block = block.next()

        self.console_output.clear()

        for text, state in new_lines:
            if state == 1:
                self._append_console(text, "error")
            else:
                self._append_console(text, "action")

        self._append_console("Console soft-refreshed (kept errors/actions).", "action")
        self._force_raise()


    def _console_hard_refresh(self):
        self.console_output.clear()
        self._append_console("Console cleared.", "action")
        self._force_raise()


    def _console_full_reset(self):
        self.console_output.clear()
        self.console_mode.setCurrentText("All")
        self._append_console("Console fully reset.", "action")
        self._force_raise()

    def _show_help_tab(self):
        """Opens a read-only tab with the keyboard shortcuts and manual."""
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Manual":
                self.tab_widget.setCurrentIndex(i)
                return

        manual_text = """
# ======================================================================
# NUKE CODE BRIDGE v0.12 - OFFICIAL MANUAL
# ======================================================================
# A multi-user, network-based Python development environment for Nuke.

[ ⌨ KEYBOARD SHORTCUTS ]
------------------------------------------------------------------------
GENERAL:
  Ctrl + S              : Save active tab to your user folder.
  Ctrl + Enter          : Run the entire script currently in view.
  Ctrl + Shift + Enter  : Run ONLY the text you have highlighted.
  
EDITOR:
  Ctrl + Mouse Wheel    : Zoom text in/out.
  Ctrl + 0              : Reset zoom to default (10pt).
  Tab                   : Indent selection (4 spaces).
  Shift + Tab           : Unindent selection.
  Ctrl + F              : Search within the current tab (Coming Soon).


[ 🚦 CONSOLE STATUS INDICATORS ]
------------------------------------------------------------------------
The circle in the console header tells you the state of your last run:

  ● GREY   : Idle. Waiting for code.
  ● YELLOW : Busy. Code is currently executing in Nuke.
  ● GREEN  : Success. The script finished without crashing.
  ● RED    : Error. An exception occurred. Switch view to "Errors Only".


[ 🔍 CONSOLE FILTER MODES ]
------------------------------------------------------------------------
Located at the top right of the console, use the "View" dropdown to 
manage large amounts of data:

  - ALL          : Shows everything (Prints, Actions, and Errors).
  - ERRORS ONLY  : Hides everything except Python Tracebacks.
  - ACTIONS/INFO : Shows setup messages and your "print" outputs only.


[ 📁 REPOSITORY & SHARING ]
------------------------------------------------------------------------
USER ISOLATION:
  By default, you are working in your own folder:
  {BASE_SHARED_PATH}/[Your_Username]

SHARING CODE:
  To see scripts written by teammates, change the "Select User" 
  dropdown in the sidebar to "all_users" or a specific name.

BACKUPS:
  Every time you hit Save, the tool creates a .bak file in the 
  "_backups" folder. It keeps the last 3 versions automatically.


[ 💡 PRO TIPS ]
------------------------------------------------------------------------
1. VIEWING VARIABLES: 
   Click 'Refresh Vars' to see every variable currently living in 
   your session's memory (the 'exec_namespace').

2. EXECUTION HISTORY:
   Double-click any item in the History list to instantly restore 
   that specific code snippet into a new tab.

3. TAB MANAGEMENT:
   You can have multiple scripts open. An asterisk (*) next to a 
   tab name means you have unsaved changes.
# ======================================================================
"""
        help_editor = CodeEditor()
        help_editor.setPlainText(manual_text.strip())
        help_editor.setReadOnly(True)
        help_editor.setStyleSheet("background-color: #1A1A1A; color: #9CDCFE; border-left: 4px solid #007ACC;")
        idx = self.tab_widget.addTab(help_editor, "Manual")
        self.tab_widget.setCurrentIndex(idx)

    # -----------------------------
    # Execution + History
    # -----------------------------
    def _append_console(self, text, msg_type="info"):

# --- Right Panel (Editor + Scalable Console) ---
        right_main_container = QtWidgets.QWidget()
        right_main_layout = QtWidgets.QVBoxLayout(right_main_container)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(0)

        # Vertical Splitter (Editor vs Console)
        self.right_vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        
        # Editor Tabs
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.right_vertical_splitter.addWidget(self.tab_widget)

        # --- Console Area ---
        console_container = QtWidgets.QWidget()
        console_v_layout = QtWidgets.QVBoxLayout(console_container)
        console_v_layout.setContentsMargins(0, 2, 0, 0)
        
        console_header = QtWidgets.QHBoxLayout()
        
        # Status Light (Circle)
        self.status_light = QtWidgets.QLabel("●")
        self.status_light.setStyleSheet("color: #555; font-size: 18px; margin-right: 5px;")
        console_header.addWidget(self.status_light)
        
        console_header.addWidget(QtWidgets.QLabel("Console Output:"))
        console_header.addStretch()
        
        # Filter Mode Dropdown
        console_header.addWidget(QtWidgets.QLabel("View:"))
        self.console_mode = QtWidgets.QComboBox()
        self.console_mode.addItems(["All", "Errors Only", "Actions/Info"])
        self.console_mode.setFixedWidth(120)
        self.console_mode.currentIndexChanged.connect(self._apply_console_filter)
        console_header.addWidget(self.console_mode)
        
        console_v_layout.addLayout(console_header)
        
        self.console_output = QtWidgets.QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #1A1A1A; color: #D4D4D4;")
        self.console_output.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        console_v_layout.addWidget(self.console_output)
        
        self.right_vertical_splitter.addWidget(console_container)

        # Scaling logic
        self.right_vertical_splitter.setStretchFactor(0, 4)
        self.right_vertical_splitter.setStretchFactor(1, 1)
        self.right_vertical_splitter.setCollapsible(0, False)
        self.right_vertical_splitter.setCollapsible(1, False)

        right_main_layout.addWidget(self.right_vertical_splitter, 1)

        # Buttons (Bottom of Right Panel)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(4, 6, 4, 4)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.save_script)

        self.save_as_btn = QtWidgets.QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.save_script_as)

        self.run_btn = QtWidgets.QPushButton("Run Code")
        self.run_btn.clicked.connect(self.execute_code)

        self.run_sel_btn = QtWidgets.QPushButton("Run Selection")
        self.run_sel_btn.clicked.connect(self.execute_selection)

        self.refresh_vars_btn = QtWidgets.QPushButton("Refresh Vars")
        self.refresh_vars_btn.clicked.connect(self.refresh_variables)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.save_as_btn)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.run_sel_btn)
        btn_layout.addWidget(self.refresh_vars_btn)

        # ------------------------------------------------------------
        # FIRST: Create the menu
        # ------------------------------------------------------------
        self.refresh_console_menu = QtWidgets.QMenu(self)
        soft_action = self.refresh_console_menu.addAction("Soft Refresh (keep errors/actions)")
        hard_action = self.refresh_console_menu.addAction("Hard Refresh (clear console)")
        reset_action = self.refresh_console_menu.addAction("Full Reset (console + filters)")

        soft_action.triggered.connect(self._console_soft_refresh)
        hard_action.triggered.connect(self._console_hard_refresh)
        reset_action.triggered.connect(self._console_full_reset)

        # ------------------------------------------------------------
        # SECOND: Create the button and attach the menu
        # ------------------------------------------------------------
        self.refresh_console_btn = QtWidgets.QPushButton("Refresh Console")
        self.refresh_console_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D30;
                color: #9CDCFE;
                border: 1px solid #3C3C3C;
                padding: 4px 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
        """)
        self.refresh_console_btn.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.refresh_console_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
        self.refresh_console_btn.setMenu(self.refresh_console_menu)

        btn_layout.addWidget(self.refresh_console_btn)

        btn_layout.addStretch(1)
        right_main_layout.addLayout(btn_layout)


        # Final horizontal splitter setup
        self.main_horizontal_splitter.addWidget(right_main_container)
        self.main_horizontal_splitter.setStretchFactor(1, 1)

        # Status Bar (Bottom)
        self.status_bar = QtWidgets.QLabel()
        self.status_bar.setStyleSheet("font-size: 10px; color: #888; border-top: 1px solid #333;")
        main_layout.addWidget(self.status_bar)

        # Set up Shortcuts
        self.save_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_script)

        self.run_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.run_shortcut.activated.connect(self.execute_code)

        self.run_sel_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Return"), self)
        self.run_sel_shortcut.activated.connect(self.execute_selection)

        self._new_tab("Untitled")

    # -----------------------------
    # Execution + Console Logic
    # -----------------------------
    def _append_console(self, text, msg_type="info"):
        if not text: return

        self.console_output.moveCursor(QtGui.QTextCursor.End)
        fmt = QtGui.QTextCharFormat()
        colors = {"info": "#D4D4D4", "error": "#F44747", "action": "#9CDCFE"}
        
        fmt.setForeground(QtGui.QColor(colors.get(msg_type, "#D4D4D4")))
        self.console_output.setCurrentCharFormat(fmt)
        self.console_output.insertPlainText(text + "\n")
        
        block = self.console_output.document().lastBlock()
        state = 1 if msg_type == "error" else 2 if msg_type == "action" else 0
        block.setUserState(state)
        
        self.console_output.ensureCursorVisible()
        self._apply_console_filter()

    def _apply_console_filter(self):
        mode = self.console_mode.currentText()
        doc = self.console_output.document()
        self.console_output.blockSignals(True)
        
        block = doc.begin()
        while block.isValid():
            state = block.userState()
            if mode == "All":
                block.setVisible(True)
            elif mode == "Errors Only":
                block.setVisible(state == 1)
            elif mode == "Actions/Info":
                block.setVisible(state == 0 or state == 2)
            block = block.next()
            
        self.console_output.blockSignals(False)
        self.console_output.viewport().update()

    def execute_code(self):
        editor = self.get_current_editor()
        if not editor: return
        code = editor.toPlainText()
        if not code.strip(): return

        self._add_to_history(code)
        self.console_output.clear()
        self.status_light.setStyleSheet("color: #CCA700; font-size: 18px;") 
        self._append_console(">>> Executing script...", "action")

        success = True
        redirector = StreamRedirector(self.console_output)
        
        try:
            with redirector:
                self._exec_in_namespace(code)
        except Exception:
            success = False
            etype, value, tb = sys.exc_info()
            err_string = "".join(traceback.format_exception(etype, value, tb))
            self._append_console("-" * 50, "error")
            self._append_console(err_string, "error")
            self._append_console("-" * 50, "error")
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        self.status_light.setStyleSheet("color: #6A9955; font-size: 18px;" if success else "color: #F44747; font-size: 18px;")
        if success: self._append_console(">>> SUCCESS: Script finished.", "info")
        self._force_raise()

    def execute_selection(self):
        editor = self.get_current_editor()
        if not editor: return
        
        cursor = editor.textCursor()
        code = cursor.selectedText()
        if not code.strip(): return

        # Fix Qt's unicode paragraph separators
        code = code.replace('\u2029', '\n').replace('\u2028', '\n')

        self.console_output.clear()
        self.status_light.setStyleSheet("color: #CCA700; font-size: 18px;")
        self._append_console(">>> Executing selection...", "action")

        success = True
        redirector = StreamRedirector(self.console_output)
        
        try:
            with redirector:
                self._exec_in_namespace(code)
        except Exception:
            success = False
            etype, value, tb = sys.exc_info()
            err_string = "".join(traceback.format_exception(etype, value, tb))
            self._append_console("-" * 30, "error")
            self._append_console(err_string, "error")
            self._append_console("-" * 30, "error")
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        self.status_light.setStyleSheet("color: #6A9955; font-size: 18px;" if success else "color: #F44747; font-size: 18px;")
        if success: self._append_console(">>> SUCCESS: Selection finished.", "info")
        self._force_raise()

    def execute_selection(self):
            editor = self.get_current_editor()
            if not editor: return
            
            # 1. Capture selection
            cursor = editor.textCursor()
            code = cursor.selectedText()
            
            # If nothing highlighted, don't do anything (or run all)
            if not code.strip():
                return

            # --- THE CRITICAL FIX ---
            # Qt's selection uses \u2029 for newlines. Python needs \n.
            # Without this, multi-line selections will ALWAYS fail.
            code = code.replace('\u2029', '\n').replace('\u2028', '\n')

            self.console_output.clear()
            self._append_console(">>> Executing selection...", "action")
            self.status_light.setStyleSheet("color: #CCA700; font-size: 18px;")

            redirector = StreamRedirector(self.console_output)
            success = True
            
            try:
                with redirector:
                    # Use the same execution logic as the main Run button
                    self._exec_in_namespace(code)
            except Exception:
                success = False
                # Force the traceback into our console manually
                etype, value, tb = sys.exc_info()
                err_string = "".join(traceback.format_exception(etype, value, tb))
                
                self._append_console("-" * 30, "error")
                self._append_console("SELECTION ERROR:", "error")
                self._append_console(err_string, "error")
                self._append_console("-" * 30, "error")
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__

            # Update status light based on success
            if success:
                self._append_console(">>> SUCCESS: Selection finished.", "info")
                self.status_light.setStyleSheet("color: #6A9955; font-size: 18px;")
            else:
                self.status_light.setStyleSheet("color: #F44747; font-size: 18px;")
            
            self._force_raise()
    # -----------------------------
    # Dirty indicator
    # -----------------------------
    def _on_editor_modified(self):
        editor = self.sender()
        idx = self.tab_widget.indexOf(editor)
        if idx == -1:
            return
        title = self.tab_widget.tabText(idx)
        if not title.endswith("*"):
            self.tab_widget.setTabText(idx, title + "*")

    def _clear_dirty_flag(self, editor):
        idx = self.tab_widget.indexOf(editor)
        if idx == -1:
            return
        title = self.tab_widget.tabText(idx)
        if title.endswith("*"):
            self.tab_widget.setTabText(idx, title[:-1])

    def _on_editor_zoom_changed(self, zoom_level):
        self.global_zoom = zoom_level

    # -----------------------------
    # Script list
    # -----------------------------
    def _on_user_changed(self, user):
        if USE_SINGLE_SHARED_FOLDER:
            self.current_repo_path = BASE_SHARED_PATH
        else:
            if user == "all_users":
                self.current_repo_path = BASE_SHARED_PATH
            else:
                self.current_repo_path = os.path.join(BASE_SHARED_PATH, user)
        ensure_directory(self.current_repo_path)
        self._refresh_script_list()
        self._update_status_bar()

    def _refresh_script_list(self):
        self.script_list.clear()
        search = self.search_edit.text().strip().lower()

        if not os.path.exists(BASE_SHARED_PATH):
            return

        items = []

        if USE_SINGLE_SHARED_FOLDER:
            try:
                for f in os.listdir(BASE_SHARED_PATH):
                    full_path = os.path.join(BASE_SHARED_PATH, f)
                    if os.path.isfile(full_path) and f.lower().endswith(".py"):
                        rel = os.path.relpath(full_path, BASE_SHARED_PATH)
                        items.append((rel, full_path))
            except Exception as e:
                self._append_console(f"Failed to list scripts: {e}")
        else:
            if self.user_combo.currentText() == "all_users":
                for root, dirs, files in os.walk(BASE_SHARED_PATH):
                    for f in files:
                        if f.lower().endswith(".py"):
                            full_path = os.path.join(root, f)
                            rel = os.path.relpath(full_path, BASE_SHARED_PATH)
                            items.append((rel, full_path))
            else:
                user_path = self.current_repo_path
                if os.path.exists(user_path):
                    try:
                        for f in os.listdir(user_path):
                            full_path = os.path.join(user_path, f)
                            if os.path.isfile(full_path) and f.lower().endswith(".py"):
                                rel = os.path.relpath(full_path, BASE_SHARED_PATH)
                                items.append((rel, full_path))
                    except Exception as e:
                        self._append_console(f"Failed to list user scripts: {e}")

        # Display scripts
        for _, full_path in sorted(items, key=lambda x: os.path.basename(x[1]).lower()):
            name = os.path.basename(full_path)

            if search and search not in name.lower():
                continue

            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, full_path)
            self.script_list.addItem(item)

        self._update_status_bar()

    def _on_script_double_clicked(self, item):
        path = item.data(QtCore.Qt.UserRole)
        self._open_script(path)

    def _on_script_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)
        
        if not item:
            return
            
        path = item.data(QtCore.Qt.UserRole)

        menu = QtWidgets.QMenu(self)
        
        # --- FIXED STYLING (No cutting off) ---
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #D4D4D4;
                border: 1px solid #454545;
                padding: 4px;
                font-family: 'Consolas', 'Segoe UI', 'Arial';
                font-size: 12px;
                min-width: 180px; /* Forces enough width for the text */
            }
            QMenu::item {
                /* Increased right padding to prevent text truncation */
                padding: 6px 30px 6px 25px;
                background-color: transparent;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #094771; 
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #454545;
                margin: 4px 8px;
            }
        """)
        
        # Add Actions with clear text
        menu.addAction("Open Folder Location", lambda: self._open_folder(path))
        menu.addSeparator()
        menu.addAction("Delete Script", lambda: self._delete_script(path))
        
        # Mapping to global position
        menu.exec_(list_widget.mapToGlobal(pos))

    def _open_folder(self, path):
        folder = os.path.dirname(path)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as e:
            self._append_console(f"Failed to open folder: {e}")

    def _delete_script(self, path):
        if not os.path.exists(path):
            return
        base = os.path.basename(path)
        msg = f"Are you sure you want to delete:\n\n{base}"
        if nuke:
            if not nuke.ask(msg):
                return
        else:
            if QtWidgets.QMessageBox.question(self, "Delete Script", msg) != QtWidgets.QMessageBox.Yes:
                return
        try:
            os.remove(path)
        except Exception as e:
            self._append_console(f"Failed to delete script: {e}")
        self._refresh_script_list()
        

    def _open_script(self, path):
        if not os.path.exists(path):
            self._append_console(f"Script not found: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self._append_console(f"Failed to open script: {e}")
            return

        title = os.path.basename(path)

        # --- ALWAYS load into the visible tab's editor ---
        current_widget = self.tab_widget.currentWidget()

        # If the current tab is NOT an editor, create one
        if not hasattr(current_widget, "setPlainText"):
            current_widget = self._create_editor("", None)
            idx = self.tab_widget.addTab(current_widget, title)
            self.tab_widget.setCurrentIndex(idx)

        # Load content
        current_widget.blockSignals(True)
        current_widget.setPlainText(content)
        current_widget.blockSignals(False)

        # Update metadata
        current_widget.file_path = path
        self.tab_widget.setTabText(self.tab_widget.currentIndex(), title)
        self.filename_edit.setText(title)
        self._clear_dirty_flag(current_widget)

        self._append_console(f"Opened: {path}")

    def _new_script(self):
        self._new_tab("Untitled")
        self.filename_edit.clear()
    # -----------------------------
    # Save Logic (Binary Hardened)
    # -----------------------------
    def _get_user_save_folder(self):
        """Always save into a per-user folder under BASE_SHARED_PATH."""
        user = self.user_combo.currentText()
        if user == "all_users":
            user = self.current_user

        folder = os.path.join(BASE_SHARED_PATH, user)
        ensure_directory(folder)
        return folder


    def save_script(self):
        editor = self.get_current_editor()
        if not editor:
            return

        code = editor.toPlainText()
        path = getattr(editor, "file_path", None)

        # 1. Overwrite existing file
        if path:
            self._save_to_path(path, code)
            self._clear_dirty_flag(editor)
            return

        # 2. New file via top bar
        file_name = self.filename_edit.text().strip()
        if not file_name:
            self._append_console("ERROR: No filename entered in the top bar.", "error")
            return

        if not file_name.lower().endswith(".py"):
            file_name += ".py"

        target_folder = self._get_user_save_folder()
        path = os.path.join(target_folder, file_name)

        self._save_to_path(path, code)

        # Update UI
        editor.file_path = path
        self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(path))
        self.filename_edit.setText(os.path.basename(path))
        self._clear_dirty_flag(editor)
        self._refresh_script_list()


    def save_script_as(self):
        editor = self.get_current_editor()
        if not editor:
            return

        code = editor.toPlainText()

        dialog = QtWidgets.QFileDialog(self, "Save Script As", self._get_user_save_folder())
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setNameFilter("Python Files (*.py)")
        dialog.setDefaultSuffix("py")

        if dialog.exec_() != QtWidgets.QFileDialog.Accepted:
            return

        path = dialog.selectedFiles()[0]
        ensure_directory(os.path.dirname(path))

        self._save_to_path(path, code)

        editor.file_path = path
        self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(path))
        self.filename_edit.setText(os.path.basename(path))
        self._clear_dirty_flag(editor)
        self._refresh_script_list()


    def _save_to_path(self, path, code):
        """Binary-safe, newline-safe, truncation-safe save."""
        # Backup BEFORE writing
        if ENABLE_BACKUPS and os.path.exists(path):
            self._create_backup(path)

        # CRITICAL FIX — ensure final newline (Qt requires this)
        if code and not code.endswith("\n"):
            code += "\n"

        try:
            raw = code.encode("utf-8")

            # FULL REPLACEMENT WRITE
            with open(path, "wb") as f:
                f.seek(0)
                f.truncate()
                f.write(raw)

            self._append_console(f"Successfully saved: {os.path.basename(path)}", "info")

        except Exception as e:
            self._append_console(f"SAVE ERROR: {str(e)}", "error")


    def _create_backup(self, file_path):
        if not ENABLE_BACKUPS:
            return

        try:
            script_dir = os.path.dirname(file_path)
            backup_root = os.path.join(script_dir, "_backups")
            ensure_directory(backup_root)

            script_name = os.path.splitext(os.path.basename(file_path))[0]
            script_backup_dir = os.path.join(backup_root, script_name)
            ensure_directory(script_backup_dir)

            # Safety check
            if not os.path.abspath(script_backup_dir).startswith(os.path.abspath(backup_root)):
                self._append_console("Backup aborted: unsafe path.", "error")
                return

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(script_backup_dir, f"{timestamp}.bak")

            shutil.copy2(file_path, backup_file)

            # Cleanup old backups
            backups = sorted([f for f in os.listdir(script_backup_dir) if f.endswith(".bak")])
            excess = len(backups) - MAX_BACKUPS
            if excess > 0:
                for i in range(excess):
                    os.remove(os.path.join(script_backup_dir, backups[i]))

            self._append_console(f"Backup created: {os.path.basename(backup_file)}", "info")

        except Exception as e:
            self._append_console(f"Backup failed: {e}", "error")

    # -----------------------------
    # Execution + History
    # -----------------------------
    def _append_console(self, text, msg_type="info"):
        """
        Appends text with metadata for filtering.
        msg_type options: "info", "error", "action"
        """
        if not text:
            return

        self.console_output.moveCursor(QtGui.QTextCursor.End)

        fmt = QtGui.QTextCharFormat()
        colors = {"info": "#D4D4D4", "error": "#F44747", "action": "#9CDCFE"}
        fmt.setForeground(QtGui.QColor(colors.get(msg_type, "#D4D4D4")))
        self.console_output.setCurrentCharFormat(fmt)

        self.console_output.insertPlainText(text + "\n")

        block = self.console_output.document().lastBlock()
        state = 0
        if msg_type == "error": state = 1
        elif msg_type == "action": state = 2
        block.setUserState(state)

        self.console_output.ensureCursorVisible()
        self._apply_console_filter()


    def _add_to_history(self, code):
        if not code.strip():
            return

        current_tab = self.tab_widget.currentWidget()
        script_path = getattr(current_tab, "file_path", None)

        self.history_items.insert(0, (code, script_path))

        if len(self.history_items) > self.max_history:
            self.history_items = self.history_items[:self.max_history]

        self._refresh_history_list()


    def _refresh_history_list(self):
        self.history_list.clear()

        for idx, (code, script_path) in enumerate(self.history_items, 1):
            first_line = code.strip().splitlines()[0] if code.strip().splitlines() else ""
            preview = first_line[:57] + ("..." if len(first_line) > 57 else "")

            item = QtWidgets.QListWidgetItem(f"{idx}: {preview}")
            item.setData(QtCore.Qt.UserRole, (code, script_path))
            self.history_list.addItem(item)

        self._update_status_bar()


    def _on_history_double_clicked(self, item):
        data = item.data(QtCore.Qt.UserRole)
        if not data:
            return

        code, script_path = data

        if script_path and os.path.exists(script_path):
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if getattr(tab, "file_path", None) == script_path:
                    self.tab_widget.setCurrentIndex(i)
                    editor = tab if isinstance(tab, QtWidgets.QPlainTextEdit) else tab.findChild(QtWidgets.QPlainTextEdit)
                    if editor:
                        editor.setPlainText(code)
                    return

        self._new_tab("History Snippet", code)


    # ---------------------------------------------------------
    # SHARED EXECUTION PIPELINE (used by full run + selection)
    # ---------------------------------------------------------
    def _run_code_block(self, code):
        self._add_to_history(code)
        self.console_output.clear()

        # Busy (yellow)
        self.status_light.setStyleSheet("color: #CCA700; font-size: 18px;")
        self._append_console(">>> Executing script...", "action")

        redirector = StreamRedirector(self.console_output)
        success = True

        try:
            with redirector:
                self._exec_in_namespace(code)

        except Exception:
            success = False
            etype, value, tb = sys.exc_info()
            err_string = "".join(traceback.format_exception(etype, value, tb))

            self._append_console("-" * 50, "error")
            self._append_console("PYTHON ERROR DETECTED:", "error")
            self._append_console(err_string, "error")
            self._append_console("-" * 50, "error")

        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        if success:
            self._append_console(">>> SUCCESS: Script finished.", "info")
            self.status_light.setStyleSheet("color: #6A9955; font-size: 18px;")
        else:
            self.status_light.setStyleSheet("color: #F44747; font-size: 18px;")

        self._force_raise()


    # -----------------------------
    # Run Full Script
    # -----------------------------
    def execute_code(self):
        editor = self.get_current_editor()
        if not editor:
            return

        code = editor.toPlainText()
        if not code.strip():
            return

        if SHOW_RUN_CONFIRMATION:
            msg = "Are you sure you want to execute this script?"
            if nuke:
                if not nuke.ask(msg):
                    return
            else:
                if QtWidgets.QMessageBox.question(self, "Run Script?", msg) != QtWidgets.QMessageBox.Yes:
                    return

        self._run_code_block(code)


    # -----------------------------
    # Run Selection (FIXED)
    # -----------------------------
    def execute_selection(self):
        editor = self.get_current_editor()
        if not editor:
            return

        cursor = editor.textCursor()
        selected = cursor.selectedText()

        if not selected.strip():
            code = editor.toPlainText()
        else:
            code = selected.replace("\u2029", "\n")

        self._run_code_block(code)


    # -----------------------------
    # Variables
    # -----------------------------
    def refresh_variables(self):
        self.vars_list.clear()
        for key, value in sorted(self.exec_namespace.items()):
            if key == "__builtins__":
                continue
            self.vars_list.addItem(f"{key} : {type(value).__name__}")

    # -----------------------------
    # Status bar
    # -----------------------------
    def _update_status_bar(self):
        repo = self.current_repo_path or BASE_SHARED_PATH
        file_count = 0
        if os.path.exists(repo):
            if USE_SINGLE_SHARED_FOLDER:
                try:
                    file_count = sum(1 for f in os.listdir(repo) if f.lower().endswith(".py"))
                except Exception:
                    pass
            else:
                for root, _, files in os.walk(repo):
                    file_count += sum(1 for f in files if f.lower().endswith(".py"))

        status = (f"Repo: {repo} | Files: {file_count} | "
                  f"Backups: {MAX_BACKUPS if ENABLE_BACKUPS else 0} | "
                  f"History: {len(self.history_items)}/{self.max_history} | "
                  f"User: {self.current_user}")
        self.status_bar.setText(status)
# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

# We define this outside the function so it stays in memory
_BRIDGE_INSTANCE = None

def start_nuke_code_bridge():
    global _BRIDGE_INSTANCE
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    # Check for existing window
    for widget in app.topLevelWidgets():
        if isinstance(widget, NukeCodeBridge):
            widget.raise_()
            widget.activateWindow()
            return widget

    # Assign to the global variable to prevent the window from disappearing
    _BRIDGE_INSTANCE = NukeCodeBridge()
    _BRIDGE_INSTANCE.resize(1200, 800)
    _BRIDGE_INSTANCE.show()
    return _BRIDGE_INSTANCE


if __name__ == "__main__":
    if nuke:
        # If in Nuke, just trigger the window
        start_nuke_code_bridge()
    else:
        # If running standalone, we need to start the event loop
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        win = start_nuke_code_bridge()
        sys.exit(app.exec_())

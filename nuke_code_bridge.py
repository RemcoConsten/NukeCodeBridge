# NukeCodeBridge v0.15
# Network-Based Script Manager & Python Editor for Foundry Nuke

from __future__ import print_function

import re
import os
import sys
import traceback
import datetime
import __main__
import shutil
import json
import time

try:
    import nuke
except ImportError:
    nuke = None

try:
    from PySide6 import QtWidgets, QtGui, QtCore
    UniversalShortcut = QtGui.QShortcut
except ImportError:
    from PySide2 import QtWidgets, QtGui, QtCore
    UniversalShortcut = QtWidgets.QShortcut

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

#base shared is the location where the shared scripts per user will be located 
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\pipeline\NukeCodeBridge"
SHOW_RUN_CONFIRMATION   = True    # ask before running code
USE_SINGLE_SHARED_FOLDER = False  # True = everyone shares one folder
ENABLE_BACKUPS          = True
MAX_BACKUPS             = 3       # how many .bak versions to keep
MAX_HISTORY_ITEMS       = 25      # Sets the number of previously run code kept in the sidebar for quick access. 
CONFIRM_OVERWRITE       = False   # True = ask before overwriting existing file

# Crash-recovery autosave interval in minutes (0 = disabled).
# Writes a lightweight .autosave file alongside each open script.
# Never touches the _backups rotation.
AUTOSAVE_INTERVAL_MINUTES = 5

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

def autosave_path(file_path):
    return file_path + ".autosave"

def user_scripts_folder(user_folder):
    """Scripts live in a scripts/ subfolder inside the user folder.
    e.g. \\YOUR_SERVER\YOUR_SHARE\pipeline\NukeCodeBridge\user.name\scripts\\"""
    folder = os.path.join(user_folder, "scripts")
    ensure_directory(folder)
    return folder

def personal_snippets_path(user_folder, username):
    """Always stores in a user-named subfolder under BASE_SHARED_PATH,
    even when USE_SINGLE_SHARED_FOLDER is True. This keeps personal
    snippets isolated from shared scripts and other users.
    e.g. \\YOUR_SERVER\YOUR_SHARE\pipeline\NukeCodeBridge\user.name\user.name_snippets.json"""
    user_dir = os.path.join(BASE_SHARED_PATH, username)
    ensure_directory(user_dir)
    return os.path.join(user_dir, f"{username}_snippets.json")

def shared_snippets_path():
    """e.g. \\YOUR_SERVER\YOUR_SHARE\pipeline\NukeCodeBridge\shared_snippets.json"""
    return os.path.join(BASE_SHARED_PATH, "shared_snippets.json")

# ------------------------------------------------------------------
# Script meta / comments utilities
# ------------------------------------------------------------------

def meta_folder(scripts_folder):
    folder = os.path.join(scripts_folder, "_meta")
    ensure_directory(folder)
    return folder

def meta_path(scripts_folder, script_name):
    name = os.path.splitext(os.path.basename(script_name))[0]
    return os.path.join(meta_folder(scripts_folder), f"{name}.meta.json")

def meta_lock_path(scripts_folder, script_name):
    name = os.path.splitext(os.path.basename(script_name))[0]
    return os.path.join(meta_folder(scripts_folder), f"{name}.meta.lock")

def read_meta(scripts_folder, script_name):
    path = meta_path(scripts_folder, script_name)
    if not os.path.exists(path):
        return {"description": "", "comments": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"description": "", "comments": []}

def write_meta(scripts_folder, script_name, data):
    lock = meta_lock_path(scripts_folder, script_name)
    path = meta_path(scripts_folder, script_name)
    for _ in range(3):
        if not os.path.exists(lock): break
        try:
            if time.time() - os.path.getmtime(lock) > 10:
                os.remove(lock); break
        except Exception: pass
        time.sleep(0.5)
    try:
        with open(lock, "w") as f: f.write(str(os.getpid()))
        with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    finally:
        try:
            if os.path.exists(lock): os.remove(lock)
        except Exception: pass

BUILTIN_SNIPPETS = [
    {"trigger": "fornode", "title": "For Each Node",     "category": "Python",
     "body": "for node in nuke.selectedNodes():\n    $CURSOR$"},
    {"trigger": "ifnuke",  "title": "If Nuke Available", "category": "Python",
     "body": "if nuke:\n    $CURSOR$"},
    {"trigger": "tryex",   "title": "Try / Except",      "category": "Python",
     "body": "try:\n    $CURSOR$\nexcept Exception as e:\n    print(e)"},
    {"trigger": "defn",    "title": "Define Function",   "category": "Python",
     "body": "def $CURSOR$(args):\n    pass"},
    {"trigger": "blink",   "title": "Blink Kernel",      "category": "Blink",
     "body": "kernel $CURSOR$ : ImageComputationKernel<ePixelWise>\n{\n  Image<eRead, eAccessPoint> src;\n  Image<eWrite> dst;\n\n  void process() {\n    dst() = src();\n  }\n};"},
    {"trigger": "blinkp",  "title": "Blink Param",       "category": "Blink",
     "body": "param:\n  float $CURSOR$;\n\n  local:\n  float _value;"},
]

# ----------------------------------------------------------------------
# Stream Redirector
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
# Code Editor
# ----------------------------------------------------------------------

class CodeEditor(QtWidgets.QPlainTextEdit):
    zoomChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        font = QtGui.QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.setFont(font)
        self._default_point_size = font.pointSize()
        self._current_zoom = 0

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                selection-background-color: #264F78;
                border: none;
            }
        """)

        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._current_line_color = QtGui.QColor(60, 60, 60, 80)
        self._line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.highlightOccurrences)
        self.horizontalScrollBar().valueChanged.connect(lambda: self.viewport().update())
        self.verticalScrollBar().valueChanged.connect(lambda: self.viewport().update())
        self.textChanged.connect(lambda: self.viewport().update())
        self.cursorPositionChanged.connect(lambda: self.viewport().update())
        self.updateLineNumberAreaWidth(0)

        # Ensure Tab reaches our keyPressEvent instead of being swallowed
        # by Qt's focus chain or the parent QTabWidget
        self.setTabChangesFocus(False)

    # ------------------------------------------------------------------
    # Line numbers
    # ------------------------------------------------------------------

    def event(self, e):
        result = super().event(e)
        if e.type() in (QtCore.QEvent.FontChange, QtCore.QEvent.Resize,
                        QtCore.QEvent.LayoutRequest, QtCore.QEvent.UpdateRequest):
            self.updateLineNumberAreaWidth(0)
        return result

    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        return 40 + self.fontMetrics().horizontalAdvance("9") * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
        self.updateGeometry()
        self.document().setDocumentMargin(2)
        self.viewport().update()

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._line_number_area.setGeometry(0, 0, self.lineNumberAreaWidth(), self.height())

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor(35, 35, 35))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = int(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QtGui.QColor(133, 133, 133))
                painter.drawText(0, top, self.lineNumberAreaWidth() - 15,
                                 self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                                 str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ------------------------------------------------------------------
    # Indent guides
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.setPen(QtGui.QColor(255, 255, 255, 28))
        indent_width = self.fontMetrics().horizontalAdvance(" ") * 4
        block = self.firstVisibleBlock()
        offset = self.contentOffset()
        while block.isValid():
            geom = self.blockBoundingGeometry(block).translated(offset)
            top, bottom = int(geom.top()), int(geom.bottom())
            if top > self.viewport().rect().bottom():
                break
            text = block.text()
            cursor = QtGui.QTextCursor(block)
            cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
            while cursor.positionInBlock() < len(text) and text[cursor.positionInBlock()].isspace():
                cursor.movePosition(QtGui.QTextCursor.NextCharacter)
            first_x = self.cursorRect(cursor).left()
            start_x = self.cursorRect(QtGui.QTextCursor(block)).left()
            indent_level = max(0, int((first_x - start_x) // indent_width))
            for i in range(indent_level):
                gx = start_x + i * indent_width
                if gx > 0:
                    painter.drawLine(int(gx), top, int(gx), bottom)
            block = block.next()
        painter.end()

    # ------------------------------------------------------------------
    # Highlight
    # ------------------------------------------------------------------

    def highlightCurrentLine(self):
        existing = [s for s in self.extraSelections()
                    if not s.format.property(QtGui.QTextFormat.FullWidthSelection)]
        if not self.isReadOnly():
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format.setBackground(self._current_line_color)
            sel.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            self.setExtraSelections([sel] + existing)
        else:
            self.setExtraSelections(existing)

    def highlightOccurrences(self):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
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

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def wheelEvent(self, event):
        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier:
            if event.angleDelta().y() > 0:
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

    # ------------------------------------------------------------------
    # Keys
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        key, mods = event.key(), event.modifiers()
        if mods & QtCore.Qt.ControlModifier:
            if key in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal): self.zoomIn(1); return
            if key == QtCore.Qt.Key_Minus: self.zoomOut(1); return
            if key == QtCore.Qt.Key_0: self.reset_zoom(); return
        if key in (QtCore.Qt.Key_Space, QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self._hide_snippet_highlight()
        if key == QtCore.Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._indent_selection(cursor)
            else:
                # Check for snippet trigger word before falling back to indent
                if self._try_expand_snippet(cursor):
                    return
                self.insertPlainText(" " * 4)
            return
        if key == QtCore.Qt.Key_Backtab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._unindent_selection(cursor)
            else:
                self._unindent_current_line(cursor)
            return
        super().keyPressEvent(event)

    def _try_expand_snippet(self, cursor):
        """If word left of cursor matches a snippet trigger, expand it.
        Returns True if a snippet was expanded."""
        tc = QtGui.QTextCursor(cursor)
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        word = tc.selectedText().strip()
        if not word:
            return False

        parent = getattr(self, "_bridge", None) or self.parent()
        if not parent or not hasattr(parent, "_get_all_snippets"):
            return False

        for snippet in parent._get_all_snippets():
            if snippet.get("trigger", "") == word:
                body = snippet.get("body", "")
                # Detect current indentation level
                block_text = cursor.block().text()
                indent = len(block_text) - len(block_text.lstrip())
                indent_str = " " * indent
                # Apply current indent to every line after the first
                lines = body.split("\n")
                indented_lines = [lines[0]] + [
                    indent_str + l if l else l for l in lines[1:]
                ]
                expanded = "\n".join(indented_lines)

                # Replace trigger word with expanded snippet
                tc.beginEditBlock()
                tc.removeSelectedText()
                tc.insertText(expanded)
                tc.endEditBlock()

                # Move cursor to $CURSOR$ placeholder if present
                doc_text = self.toPlainText()
                placeholder_pos = doc_text.find("$CURSOR$")
                if placeholder_pos != -1:
                    # Remove the placeholder and position cursor there
                    final_cursor = QtGui.QTextCursor(self.document())
                    final_cursor.setPosition(placeholder_pos)
                    final_cursor.setPosition(placeholder_pos + len("$CURSOR$"),
                                             QtGui.QTextCursor.KeepAnchor)
                    final_cursor.removeSelectedText()
                    self.setTextCursor(final_cursor)
                return True
        return False

    def _get_trigger_at_cursor(self):
        """Return snippet dict if word under cursor matches a trigger, else None."""
        cursor = self.textCursor()
        tc = QtGui.QTextCursor(cursor)
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        word = tc.selectedText().strip()
        if not word:
            return None
        parent = getattr(self, "_bridge", None) or self.parent()
        if not parent or not hasattr(parent, "_get_all_snippets"):
            return None
        for snippet in parent._get_all_snippets():
            if snippet.get("trigger", "") == word:
                return snippet
        return None

    def _show_snippet_highlight(self):
        """Highlight the trigger word with an amber background."""
        cursor = self.textCursor()
        tc = QtGui.QTextCursor(cursor)
        tc.select(QtGui.QTextCursor.WordUnderCursor)

        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(QtGui.QColor("#CCA700"))
        fmt.setForeground(QtGui.QColor("#1E1E1E"))  # dark text on amber

        sel = QtWidgets.QTextEdit.ExtraSelection()
        sel.cursor = tc
        sel.format = fmt
        sel.format.setProperty(999, "snippet_highlight")  # tag for removal

        # Keep non-snippet selections, replace any previous snippet highlight
        existing = [s for s in self.extraSelections()
                    if s.format.property(999) != "snippet_highlight"]
        self.setExtraSelections(existing + [sel])

    def _hide_snippet_highlight(self):
        """Remove the snippet highlight extra selection."""
        cleaned = [s for s in self.extraSelections()
                   if s.format.property(999) != "snippet_highlight"]
        self.setExtraSelections(cleaned)

    def _show_snippet_popup(self, snippet):
        self._show_snippet_highlight()

    def _hide_snippet_popup(self):
        self._hide_snippet_highlight()

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
            if block == end: break
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
            if block == end: break
            block = block.next()
        cursor.endEditBlock()

    def _unindent_current_line(self, cursor):
        cursor.beginEditBlock()
        self._unindent_block(cursor.block())
        cursor.endEditBlock()

    def _unindent_block(self, block):
        text = block.text()
        if not text: return
        remove = 0
        for ch in text:
            if ch in (" ", "\t") and remove < 4: remove += 1
            else: break
        if remove == 0: return
        tc = QtGui.QTextCursor(block)
        tc.movePosition(QtGui.QTextCursor.StartOfBlock)
        for _ in range(remove):
            tc.deleteChar()


# ----------------------------------------------------------------------
# Syntax Highlighter
# ----------------------------------------------------------------------

class PythonHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        def fmt(color, bold=False):
            f = QtGui.QTextCharFormat()
            f.setForeground(QtGui.QColor(color))
            if bold: f.setFontWeight(QtGui.QFont.Bold)
            return f

        kw = fmt("#C586C0")
        for k in ["def","class","import","from","return","if","elif","else",
                  "try","except","finally","for","while","in","and","or",
                  "not","pass","break","continue","with","as","lambda",
                  "yield","assert","del","global","nonlocal","raise","is"]:
            self.rules.append((rf"\b{k}\b", kw))

        bi = fmt("#9CDCFE")
        for b in ["print","len","range","dict","list","set","tuple","int",
                  "float","str","bool","type","dir","help","isinstance",
                  "issubclass","open","super","enumerate","zip","map",
                  "filter","sum","min","max","abs"]:
            self.rules.append((rf"\b{b}\b", bi))

        self.rules += [
            (r'"[^"\\]*(\\.[^"\\]*)*"', fmt("#CE9178")),
            (r"'[^'\\]*(\\.[^'\\]*)*'", fmt("#CE9178")),
            (r"#.*",                    fmt("#6A9955")),
            (r"@\w+",                   fmt("#C8C8C8")),
            (r"\bclass\s+(\w+)",        fmt("#4EC9B0", bold=True)),
            (r"\bdef\s+(\w+)",          fmt("#DCDCAA")),
            (r"\b[0-9]+\b",            fmt("#B5CEA8")),
            (r"[+\-*/%=<>!]+",         fmt("#D4D4D4")),
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text):
                s, e = m.span()
                self.setFormat(s, e - s, fmt)


# ----------------------------------------------------------------------
# Go To Line Dialog
# ----------------------------------------------------------------------

class GoToLineDialog(QtWidgets.QDialog):
    def __init__(self, max_line, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Go to Line")
        self.setFixedSize(250, 80)
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Line:"))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setMaximum(max_line)
        layout.addWidget(self.spin)
        btn = QtWidgets.QPushButton("Go")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def line_number(self):
        return self.spin.value()


# ----------------------------------------------------------------------
# Snippet Manager Dialog
# ----------------------------------------------------------------------

class SnippetManagerDialog(QtWidgets.QDialog):
    """Manage personal and shared snippets."""

    CATEGORIES = ["Python", "Blink", "Custom"]

    def __init__(self, bridge):
        super().__init__(bridge)
        self.bridge = bridge
        self.setWindowTitle("Snippet Manager")
        self.resize(900, 580)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #2D2D2D;
                color: #D4D4D4;
            }
            QListWidget {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
            }
            QLineEdit, QComboBox, QPlainTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
                padding: 2px;
            }
            QPushButton {
                background-color: #3C3C3C;
                color: #D4D4D4;
                border: 1px solid #555;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
                border: 1px solid #007ACC;
            }
            QPushButton:disabled {
                color: #666;
                background-color: #2D2D2D;
            }
            QLabel { color: #D4D4D4; }
            QSplitter::handle { background-color: #3C3C3C; }
            QFormLayout QLabel { color: #9CDCFE; }
        """)
        self._personal = bridge._load_personal_snippets()
        self._shared   = bridge._load_shared_snippets()
        self._init_ui()
        # Connect pool/filter signals AFTER ui is built so _refresh_lists
        # doesn't fire before buttons exist
        self.pool_combo.currentIndexChanged.connect(self._refresh_lists)
        self.cat_filter.currentIndexChanged.connect(self._refresh_lists)
        self._refresh_lists()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Top: pool selector
        pool_row = QtWidgets.QHBoxLayout()
        pool_row.addWidget(QtWidgets.QLabel("Pool:"))
        self.pool_combo = QtWidgets.QComboBox()
        self.pool_combo.addItems(["Personal", "Shared", "Built-in (read-only)"])
        pool_row.addWidget(self.pool_combo)
        pool_row.addStretch()

        # Category filter
        pool_row.addWidget(QtWidgets.QLabel("Category:"))
        self.cat_filter = QtWidgets.QComboBox()
        self.cat_filter.addItems(["All"] + self.CATEGORIES)
        pool_row.addWidget(self.cat_filter)
        layout.addLayout(pool_row)

        # Main splitter: list | editor
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left: snippet list
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.snippet_list = QtWidgets.QListWidget()
        self.snippet_list.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self.snippet_list)

        list_btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("+ New")
        self.add_btn.clicked.connect(self._add_snippet)
        self.del_btn = QtWidgets.QPushButton("Delete")
        self.del_btn.clicked.connect(self._delete_snippet)
        open_loc_btn = QtWidgets.QPushButton("📂 Location")
        open_loc_btn.setToolTip("Open the folder containing this snippet file")
        open_loc_btn.clicked.connect(self._open_snippets_location)
        list_btns.addWidget(self.add_btn)
        list_btns.addWidget(self.del_btn)
        list_btns.addWidget(open_loc_btn)
        left_layout.addLayout(list_btns)
        splitter.addWidget(left)

        # Right: editor
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        form = QtWidgets.QFormLayout()
        self.title_edit   = QtWidgets.QLineEdit()
        self.trigger_edit = QtWidgets.QLineEdit()
        self.trigger_edit.setPlaceholderText("e.g. mysnip  (Tab to expand)")
        self.cat_edit     = QtWidgets.QComboBox()
        self.cat_edit.addItems(self.CATEGORIES)
        self.cat_edit.setEditable(True)  # allow custom categories

        form.addRow("Title:",    self.title_edit)
        form.addRow("Trigger:",  self.trigger_edit)
        form.addRow("Category:", self.cat_edit)
        right_layout.addLayout(form)

        right_layout.addWidget(QtWidgets.QLabel(
            "Code body  (use $CURSOR$ to mark where cursor lands after expansion):"
        ))
        self.body_edit = QtWidgets.QPlainTextEdit()
        self.body_edit.setStyleSheet(
            "background:#1E1E1E; color:#D4D4D4; font-family:Consolas; font-size:10pt;"
        )
        right_layout.addWidget(self.body_edit, 1)

        save_row = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Save Changes")
        self.save_btn.clicked.connect(self._save_current)
        self.insert_btn = QtWidgets.QPushButton("Insert into Editor")
        self.insert_btn.clicked.connect(self._insert_into_editor)
        self.move_shared_btn = QtWidgets.QPushButton("→ Move to Shared")
        self.move_shared_btn.setToolTip("Copy this snippet to the shared pool and remove it from personal")
        self.move_shared_btn.clicked.connect(self._move_to_shared)
        save_row.addWidget(self.save_btn)
        save_row.addWidget(self.insert_btn)
        save_row.addWidget(self.move_shared_btn)
        save_row.addStretch()
        right_layout.addLayout(save_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

        # Bottom
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    # ------------------------------------------------------------------

    def _current_pool(self):
        return self.pool_combo.currentText()

    def _current_data(self):
        pool = self._current_pool()
        if pool == "Personal":     return self._personal
        if pool == "Shared":       return self._shared
        return BUILTIN_SNIPPETS  # read-only

    def _refresh_lists(self):
        self.snippet_list.clear()
        cat_filter = self.cat_filter.currentText()
        is_readonly = self._current_pool() == "Built-in (read-only)"
        for attr in ("add_btn", "del_btn", "save_btn"):
            btn = getattr(self, attr, None)
            if btn:
                btn.setEnabled(not is_readonly)
        # Move to Shared only makes sense when viewing Personal pool
        msb = getattr(self, "move_shared_btn", None)
        if msb:
            msb.setEnabled(self._current_pool() == "Personal")

        # Store the real index into the pool list so we can mutate by index
        for pool_idx, s in enumerate(self._current_data()):
            if cat_filter != "All" and s.get("category", "") != cat_filter:
                continue
            label = f"[{s.get('category','?')}]  {s.get('trigger','')}  —  {s.get('title','')}"
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, pool_idx)   # store index, not dict
            self.snippet_list.addItem(item)

        self._clear_form()

    def _clear_form(self):
        self.title_edit.clear()
        self.trigger_edit.clear()
        self.body_edit.clear()

    def _on_select(self, row):
        item = self.snippet_list.item(row)
        if not item: return
        pool_idx = item.data(QtCore.Qt.UserRole)
        data = self._current_data()
        if pool_idx is None or pool_idx >= len(data): return
        s = data[pool_idx]
        self.title_edit.setText(s.get("title", ""))
        self.trigger_edit.setText(s.get("trigger", ""))
        idx = self.cat_edit.findText(s.get("category", "Python"))
        self.cat_edit.setCurrentIndex(idx if idx >= 0 else 0)
        self.body_edit.setPlainText(s.get("body", ""))

    def _add_snippet(self):
        new_snippet = {"trigger": "newsnip", "title": "New Snippet",
                       "category": "Python", "body": ""}
        pool = self._current_pool()
        if pool == "Personal":
            self._personal.append(new_snippet)
            self.bridge._save_personal_snippets(self._personal)
        else:
            self._shared.append(new_snippet)
            self.bridge._save_shared_snippets(self._shared)
        self._refresh_lists()
        last_row = self.snippet_list.count() - 1
        if last_row >= 0:
            self.snippet_list.setCurrentRow(last_row)
            self._on_select(last_row)

    def _delete_snippet(self):
        item = self.snippet_list.currentItem()
        if not item: return
        row = self.snippet_list.currentRow()
        pool_idx = item.data(QtCore.Qt.UserRole)
        pool = self._current_pool()

        # Get snippet name for confirmation
        data = self._current_data()
        if pool_idx is None or pool_idx >= len(data): return
        name = data[pool_idx].get("trigger", "this snippet")

        # Confirmation — always required before deleting
        msg = f"Are you sure you want to delete '{name}' from the {pool} pool?\n\nThis only removes it from the snippet JSON file."
        confirmed = QtWidgets.QMessageBox.question(
            self, "Delete Snippet", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) == QtWidgets.QMessageBox.Yes
        if not confirmed:
            return

        if pool == "Personal" and pool_idx < len(self._personal):
            del self._personal[pool_idx]
            self.bridge._save_personal_snippets(self._personal)
        elif pool == "Shared" and pool_idx < len(self._shared):
            del self._shared[pool_idx]
            self.bridge._save_shared_snippets(self._shared)
        else:
            return
        self._refresh_lists()
        new_row = min(row, self.snippet_list.count() - 1)
        if new_row >= 0:
            self.snippet_list.setCurrentRow(new_row)
            self._on_select(new_row)

    def _open_snippets_location(self):
        pool = self._current_pool()
        if pool == "Personal":
            path = personal_snippets_path(
                self.bridge.current_repo_path, self.bridge.current_user
            )
            folder = os.path.dirname(path)  # always the user subfolder
        elif pool == "Shared":
            path = shared_snippets_path()
            folder = os.path.dirname(path)
        else:
            QtWidgets.QMessageBox.information(
                self, "Built-in Snippets",
                "Built-in snippets are defined in the NukeCodeBridge script itself "
                "and have no file on disk."
            )
            return
        if not os.path.exists(path):
            QtWidgets.QMessageBox.information(
                self, "File Not Found",
                f"No snippet file exists yet at:\n{path}\n\nIt will be created automatically when you save your first snippet."
            )
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", str(e))

    def _save_current(self):
        item = self.snippet_list.currentItem()
        if not item:
            # No selection — create a new snippet from whatever is in the form
            trigger = self.trigger_edit.text().strip()
            if not trigger:
                QtWidgets.QMessageBox.information(
                    self, "No Trigger",
                    "Please fill in at least the Trigger field before saving."
                )
                return
            new_snippet = {
                "trigger":  trigger,
                "title":    self.title_edit.text().strip() or trigger,
                "category": self.cat_edit.currentText().strip() or "Python",
                "body":     self.body_edit.toPlainText(),
            }
            pool = self._current_pool()
            if pool == "Personal":
                self._personal.append(new_snippet)
                self.bridge._save_personal_snippets(self._personal)
            elif pool == "Shared":
                self._shared.append(new_snippet)
                self.bridge._save_shared_snippets(self._shared)
            self._refresh_lists()
            last = self.snippet_list.count() - 1
            if last >= 0:
                self.snippet_list.setCurrentRow(last)
                self._on_select(last)
            self.bridge._append_console(f"Snippet '{trigger}' created.", "action")
            return
        row = self.snippet_list.currentRow()
        pool_idx = item.data(QtCore.Qt.UserRole)
        pool = self._current_pool()
        data = self._current_data()
        if pool_idx is None or pool_idx >= len(data): return
        # Mutate the actual dict in the pool list by index
        data[pool_idx]["title"]    = self.title_edit.text().strip()
        data[pool_idx]["trigger"]  = self.trigger_edit.text().strip()
        data[pool_idx]["category"] = self.cat_edit.currentText().strip()
        data[pool_idx]["body"]     = self.body_edit.toPlainText()
        if pool == "Personal":
            self.bridge._save_personal_snippets(self._personal)
        elif pool == "Shared":
            self.bridge._save_shared_snippets(self._shared)
        trigger = data[pool_idx]["trigger"]
        self._refresh_lists()
        if row < self.snippet_list.count():
            self.snippet_list.setCurrentRow(row)
            self._on_select(row)
        self.bridge._append_console(
            f"Snippet '{trigger}' saved to {pool.lower()} pool.", "action"
        )

    def _move_to_shared(self):
        """Copy the selected personal snippet to the shared pool, then remove from personal."""
        item = self.snippet_list.currentItem()
        if not item: return
        pool_idx = item.data(QtCore.Qt.UserRole)
        if pool_idx is None or pool_idx >= len(self._personal): return

        snippet = dict(self._personal[pool_idx])  # copy

        # Check for trigger conflict in shared pool
        existing_triggers = [s.get("trigger") for s in self._shared]
        trigger = snippet.get("trigger", "")
        if trigger in existing_triggers:
            QtWidgets.QMessageBox.warning(
                self, "Trigger Conflict",
                f"A shared snippet with trigger '{trigger}' already exists. Rename it before moving."
            )
            return

        confirmed = QtWidgets.QMessageBox.question(
            self, "Move to Shared",
            f"Move '{trigger}' to the shared pool? It will be removed from your personal snippets.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) == QtWidgets.QMessageBox.Yes
        if not confirmed: return

        # Add to shared, remove from personal
        self._shared.append(snippet)
        self.bridge._save_shared_snippets(self._shared)
        del self._personal[pool_idx]
        self.bridge._save_personal_snippets(self._personal)

        self.bridge._append_console(
            f"Snippet '{snippet['trigger']}' moved to shared pool.", "action"
        )
        self._refresh_lists()

    def _insert_into_editor(self):
        """Insert snippet body at cursor in the NukeCodeBridge editor tab."""
        body = self.body_edit.toPlainText()
        if not body: return
        # Walk up to find the NukeCodeBridge parent window
        bridge = self.bridge
        editor = bridge.get_current_editor()
        if not editor: return
        cursor = editor.textCursor()
        cursor.insertText(body)
        editor.setTextCursor(cursor)
        # Don't close the dialog — let user insert multiple snippets
        bridge._append_console("Snippet inserted into editor.", "action")


# ----------------------------------------------------------------------
# Main UI
# ----------------------------------------------------------------------

class NukeCodeBridge(QtWidgets.QWidget):
    def __init__(self, parent=None):
        if parent is None:
            parent = QtWidgets.QApplication.activeWindow()

        super().__init__(parent)
        self.setWindowTitle("NukeCodeBridge v0.15")
        self.exec_namespace = {}
        if nuke:
            self.exec_namespace["nuke"] = nuke
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.raise_()
        self.activateWindow()

        self.current_user = get_user_name()
        self.current_repo_path = None
        self.global_zoom = 0
        self._recently_closed = []      # [(title, content, file_path), ...]
        self._pipette_active = False       # True while waiting for node pick
        self._pipette_ignore_nodes = set() # nodes selected BEFORE countdown
        self._last_nuke_selection = []     # cache for Edit knobChanged
        self._current_meta_script = None   # path of script whose meta is shown

        self._init_paths()
        self._init_state()
        self._init_ui()
        self._refresh_script_list()
        self._update_status_bar()
        self._restore_session_state()
        self._start_autosave_timer()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _force_raise(self):
        QtCore.QTimer.singleShot(120, self.raise_)
        QtCore.QTimer.singleShot(120, self.activateWindow)

    def showEvent(self, event):
        """Cache Nuke selection for Edit knobChanged — not during pipette."""
        super().showEvent(event)
        if nuke and not self._pipette_active:
            try:
                sel = nuke.selectedNodes()
                if sel: self._last_nuke_selection = sel
            except Exception: pass

    def _get_nuke_selected_nodes(self):
        """For Edit knobChanged: live selection with cache fallback."""
        if not nuke: return []
        try:
            sel = nuke.selectedNodes()
            if sel:
                self._last_nuke_selection = sel
                return sel
            if self._last_nuke_selection:
                all_nodes = nuke.allNodes()
                valid = [n for n in self._last_nuke_selection if n in all_nodes]
                if valid: return valid
        except Exception: pass
        return []

    def _toggle_group(self, group, body):
        """Toggle a QGroupBox body widget and flip the ▶/▼ arrow in the title."""
        visible = body.isVisible()
        body.setVisible(not visible)
        title = group.title()
        if visible:
            group.setTitle(title.replace("▼", "▶"))
        else:
            group.setTitle(title.replace("▶", "▼"))
        if group is getattr(self, "info_group", None):
            if self._info_body.isVisible():  # just became visible
                self._mark_comments_read()
            QtCore.QTimer.singleShot(0, self._update_info_group_title)

    def _exec_in_namespace(self, code):
        exec(code, self.exec_namespace)

    # ------------------------------------------------------------------
    # Crash-recovery autosave
    # Only writes a .autosave file alongside the real script.
    # Never modifies _backups. Deleted automatically on clean save/open.
    # ------------------------------------------------------------------

    def _start_autosave_timer(self):
        if AUTOSAVE_INTERVAL_MINUTES <= 0:
            return
        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.setInterval(AUTOSAVE_INTERVAL_MINUTES * 60 * 1000)
        self._autosave_timer.timeout.connect(self._run_autosave)
        self._autosave_timer.start()

    def _run_autosave(self):
        saved = 0
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            path = getattr(editor, "file_path", None)
            if not path:
                continue
            # Only autosave if the tab is dirty (has unsaved changes)
            title = self.tab_widget.tabText(i)
            if not title.endswith("*"):
                continue
            try:
                aspath = autosave_path(path)
                with open(aspath, "w", encoding="utf-8") as f:
                    f.write(editor.toPlainText())
                saved += 1
            except Exception:
                pass
        if saved:
            self._append_console(f"Autosave: {saved} file(s) crash-protected.", "action")

    def _clear_autosave(self, file_path):
        """Remove .autosave file after a clean manual save."""
        aspath = autosave_path(file_path)
        if os.path.exists(aspath):
            try:
                os.remove(aspath)
            except Exception:
                pass

    def _check_autosave_on_open(self, file_path, editor):
        """Silently flag tabs with a newer autosave. No dialog — just a tab indicator."""
        aspath = autosave_path(file_path)
        if not os.path.exists(aspath): return
        try:
            threshold = max(30, (AUTOSAVE_INTERVAL_MINUTES * 60) // 2)
            if os.path.getmtime(aspath) - os.path.getmtime(file_path) < threshold:
                os.remove(aspath); return
        except Exception: return
        editor._has_autosave = True
        idx = self.tab_widget.indexOf(editor)
        if idx != -1:
            title = self.tab_widget.tabText(idx).lstrip("[!] ")
            self.tab_widget.setTabText(idx, "⚠ " + title)
            self.tab_widget.setTabToolTip(idx, "Crash recovery — right-click tab to restore or discard")
        self._append_console(
            f"⚠ Autosave found for {os.path.basename(file_path)} — right-click the tab.",
            "action"
        )

    # ------------------------------------------------------------------
    # Search & Replace
    # ------------------------------------------------------------------

    def _show_search_bar(self):
        self.search_bar_widget.show()
        self.editor_search_edit.setFocus()
        self.editor_search_edit.selectAll()

    def _do_editor_search(self):
        editor = self.get_current_editor()
        if not editor: return
        text = self.editor_search_edit.text()
        if text: editor.find(text)

    def _find_next(self):
        editor = self.get_current_editor()
        if not editor: return
        text = self.editor_search_edit.text()
        if not text: return
        if not editor.find(text):
            editor.moveCursor(QtGui.QTextCursor.Start)
            editor.find(text)

    def _find_prev(self):
        editor = self.get_current_editor()
        if not editor: return
        text = self.editor_search_edit.text()
        if not text: return
        if not editor.find(text, QtGui.QTextDocument.FindBackward):
            editor.moveCursor(QtGui.QTextCursor.End)
            editor.find(text, QtGui.QTextDocument.FindBackward)

    def _replace_next(self):
        editor = self.get_current_editor()
        if not editor: return
        search_text = self.editor_search_edit.text()
        if not search_text: return
        cursor = editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == search_text:
            cursor.insertText(self.editor_replace_edit.text())
        self._find_next()

    def _replace_all(self):
        editor = self.get_current_editor()
        if not editor: return
        search_text = self.editor_search_edit.text()
        if not search_text:
            self._append_console("Please enter text to find.", "error"); return
        content = editor.toPlainText()
        count = content.count(search_text)
        if count == 0:
            self._append_console(f"No occurrences of '{search_text}' found.", "info"); return
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        editor.setPlainText(content.replace(search_text, self.editor_replace_edit.text()))
        cursor.endEditBlock()
        self._append_console(f"Replaced {count} occurrence(s).", "info")

    # ------------------------------------------------------------------
    # Script content search (sidebar)
    # ------------------------------------------------------------------

    def _on_search_mode_toggled(self):
        """Switch between Name and Contents mode."""
        if self.search_mode_btn.isChecked():
            self.search_mode_btn.setText("Contents")
            self.search_edit.setPlaceholderText("Search inside files...")
        else:
            self.search_mode_btn.setText("Name")
            self.search_edit.setPlaceholderText("Filter scripts...")
        # Re-run search with new mode
        self._on_search_changed(self.search_edit.text())

    def _on_search_changed(self, text):
        if self.search_mode_btn.isChecked():
            self._search_in_scripts(text)
        else:
            self._refresh_script_list()

    def _search_in_scripts(self, term=None):
        if term is None:
            term = self.search_edit.text()
        term = term.strip()
        self.script_list.clear()
        if not term:
            return
        if not os.path.exists(BASE_SHARED_PATH):
            return
        for root, _, files in os.walk(BASE_SHARED_PATH):
            for f in files:
                if not f.lower().endswith(".py"):
                    continue
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                        if term.lower() in fh.read().lower():
                            item = QtWidgets.QListWidgetItem(f"⬡ {f}")
                            item.setData(QtCore.Qt.UserRole, full_path)
                            item.setForeground(QtGui.QColor("#9CDCFE"))
                            item.setToolTip(full_path)
                            self.script_list.addItem(item)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Go to line
    # ------------------------------------------------------------------

    def _go_to_line(self):
        editor = self.get_current_editor()
        if not editor: return
        dlg = GoToLineDialog(editor.blockCount(), self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted: return
        block = editor.document().findBlockByLineNumber(dlg.line_number() - 1)
        cursor = QtGui.QTextCursor(block)
        editor.setTextCursor(cursor)
        editor.centerCursor()
        editor.setFocus()

    # ------------------------------------------------------------------
    # Session save / restore
    # ------------------------------------------------------------------

    def _save_session_state(self):
        if not self.current_repo_path: return
        session_data = []
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            title = self.tab_widget.tabText(i)
            if not getattr(editor, "file_path", None) and editor.toPlainText().strip():
                session_data.append({"title": title, "content": editor.toPlainText()})
        try:
            with open(os.path.join(self.current_repo_path, ".session_recovery.json"), "w") as f:
                json.dump(session_data, f, indent=4)
        except Exception as e:
            print("Session Save Error:", e)

    def _restore_session_state(self):
        if not self.current_repo_path: return
        buffer_path = os.path.join(self.current_repo_path, ".session_recovery.json")
        if not os.path.exists(buffer_path): return
        try:
            with open(buffer_path, "r") as f:
                session_data = json.load(f)
            if not session_data:
                return
            # Remove the blank Untitled tab that _init_ui created
            if self.tab_widget.count() == 1:
                first = self.tab_widget.widget(0)
                if not first.toPlainText().strip():
                    self.tab_widget.removeTab(0)
                    first.deleteLater()
            for item in session_data:
                self._new_tab(title=item.get("title", "Untitled"),
                              content=item.get("content", ""))
            os.remove(buffer_path)
        except Exception as e:
            print("Session Restore Error:", e)

    def closeEvent(self, event):
        self._save_session_state()
        # Clean up all autosave files on normal close — they are only
        # meaningful after a crash, not after a deliberate exit
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            path = getattr(editor, "file_path", None)
            if path:
                self._clear_autosave(path)
        event.accept()

    def _on_tab_changed(self, index):
        editor = self.tab_widget.widget(index)
        if not editor: return

        node = getattr(editor, "_editing_knobchanged_node", None)
        is_recovered = getattr(editor, "_was_knobchanged_recovered", False)

        if node is not None:
            if nuke and node in nuke.allNodes():
                self.filename_edit.setText(f"knobChanged: {node.name()}")
                self.filename_edit.setReadOnly(True)
            else:
                del editor._editing_knobchanged_node
                editor._was_knobchanged_recovered = True
                self.filename_edit.clear()
                self.filename_edit.setPlaceholderText("NODE DELETED - Use Save As")
                self.filename_edit.setReadOnly(False)
            self._update_line_col()
            return

        if is_recovered:
            self.filename_edit.clear()
            self.filename_edit.setPlaceholderText("NODE DELETED - Use Save As")
            self.filename_edit.setReadOnly(False)
            self._update_line_col()
            return

        self.filename_edit.setReadOnly(False)
        path = getattr(editor, "file_path", None)
        self.filename_edit.setText(os.path.basename(path) if path else "")
        self.filename_edit.setPlaceholderText("Enter script_name.py here...")
        self._update_line_col()

    # ------------------------------------------------------------------
    # Line / Col indicator
    # ------------------------------------------------------------------

    def _update_line_col(self):
        editor = self.get_current_editor()
        if not editor:
            self.line_col_label.setText("")
            return
        cursor = editor.textCursor()
        self.line_col_label.setText(
            f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1}"
        )

    def _update_snippet_hint(self, editor):
        """Status bar only — yellow when cursor is on a snippet trigger."""
        if not hasattr(self, "_snippet_hint_timer"):
            self._snippet_hint_timer = QtCore.QTimer(self)
            self._snippet_hint_timer.setSingleShot(True)
            self._snippet_hint_timer.timeout.connect(
                lambda: self._show_snippet_hint_now(editor)
            )
        self._snippet_hint_timer.stop()

        snippet = editor._get_trigger_at_cursor()
        if not snippet:
            # Reset immediately — no delay on hide
            self.line_col_label.setStyleSheet(
                "font-size:10px; color:#888; padding-right:10px;"
            )
            self._update_line_col()
            editor._hide_snippet_highlight()
            return

        # Debounce — only light up after 150ms so it doesn't flash while typing
        self._snippet_hint_timer.start(150)

    def _show_snippet_hint_now(self, editor):
        snippet = editor._get_trigger_at_cursor()
        if not snippet:
            return
        cursor = editor.textCursor()
        self.line_col_label.setStyleSheet(
            "font-size:10px; color:#CCA700; padding-right:10px; font-weight:bold;"
        )
        self.line_col_label.setText(
            f"Ln {cursor.blockNumber()+1}, Col {cursor.columnNumber()+1}"
            f"  ⚡ {snippet['trigger']} — Tab to expand"
        )
        editor._show_snippet_highlight()

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def _init_paths(self):
        self.current_repo_path = (
            BASE_SHARED_PATH if USE_SINGLE_SHARED_FOLDER
            else os.path.join(BASE_SHARED_PATH, self.current_user)
        )
        ensure_directory(self.current_repo_path)

    def _init_state(self):
        self.history_items = []
        self.max_history = MAX_HISTORY_ITEMS

    def _create_editor(self, content="", title=None, file_path=None, knobchanged_node=None):
        editor = CodeEditor(parent=self)
        editor.file_path = file_path
        editor._editing_knobchanged_node = knobchanged_node
        editor._bridge = self   # direct reference, survives Qt reparenting
        editor.textChanged.connect(self._save_session_state)
        editor.setPlainText(content)
        PythonHighlighter(editor.document())
        editor.cursorPositionChanged.connect(editor.highlightOccurrences)
        editor.cursorPositionChanged.connect(self._update_line_col)
        editor.cursorPositionChanged.connect(lambda: self._update_snippet_hint(editor))
        if self.global_zoom > 0:
            editor.zoomIn(self.global_zoom)
        elif self.global_zoom < 0:
            editor.zoomOut(-self.global_zoom)
        editor.textChanged.connect(self._on_editor_modified)
        editor.zoomChanged.connect(self._on_editor_zoom_changed)
        editor.textChanged.connect(self._save_session_state)
        return editor

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def _new_tab(self, title, content="", file_path=None):
        editor = self._create_editor(content, title=title, file_path=file_path)
        if not title:
            title = os.path.basename(file_path) if file_path else "Untitled"
        idx = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(idx)

    def _close_tab(self, index):
        editor = self.tab_widget.widget(index)
        title = self.tab_widget.tabText(index).rstrip("*")
        self._recently_closed.insert(0, (title, editor.toPlainText(),
                                         getattr(editor, "file_path", None)))
        self._recently_closed = self._recently_closed[:10]

        if self.tab_widget.count() == 1:
            editor.setPlainText("")
            editor.file_path = None
            editor._editing_knobchanged_node = None
            self.tab_widget.setTabText(index, "Untitled")
            return
        self.tab_widget.removeTab(index)
        editor.deleteLater()

    def _reopen_last_closed_tab(self):
        if not self._recently_closed:
            self._append_console("No recently closed tabs.", "info"); return
        title, content, file_path = self._recently_closed.pop(0)
        self._new_tab(title, content, file_path)
        self._append_console(f"Reopened: {title}", "action")

    def _duplicate_tab(self):
        editor = self.get_current_editor()
        if not editor: return
        title = self.tab_widget.tabText(self.tab_widget.currentIndex()).rstrip("*")
        self._new_tab(f"{title} (copy)", editor.toPlainText())

    def get_current_editor(self):
        return self.tab_widget.currentWidget()

    def _on_tab_bar_context_menu(self, pos):
        index = self.tab_widget.tabBar().tabAt(pos)
        if index == -1: return
        menu = QtWidgets.QMenu(self)
        editor = self.tab_widget.widget(index)
        if getattr(editor, "_has_autosave", False):
            path = getattr(editor, "file_path", None)
            if path and os.path.exists(autosave_path(path)):
                menu.addAction("⚠ Restore Autosave", lambda: self._restore_autosave(index))
                menu.addAction("✕ Discard Autosave", lambda: self._discard_autosave(index))
                menu.addSeparator()
        menu.addAction("Duplicate Tab", self._duplicate_tab)
        menu.addAction("Close Tab", lambda: self._close_tab(index))
        menu.addSeparator()
        menu.addAction("Reopen Last Closed  (Ctrl+Shift+T)", self._reopen_last_closed_tab)
        menu.exec_(self.tab_widget.tabBar().mapToGlobal(pos))

    def _restore_autosave(self, index):
        editor = self.tab_widget.widget(index)
        path = getattr(editor, "file_path", None)
        if not path: return
        aspath = autosave_path(path)
        if not os.path.exists(aspath): return
        try:
            with open(aspath, "r", encoding="utf-8") as f:
                editor.setPlainText(f.read())
            editor._has_autosave = False
            title = self.tab_widget.tabText(index).lstrip("[!] ")
            self.tab_widget.setTabText(index, title)
            self.tab_widget.setTabToolTip(index, "")
            os.remove(aspath)
            self._append_console(f"Autosave restored: {os.path.basename(path)}", "action")
        except Exception as e:
            self._append_console(f"Restore failed: {e}", "error")

    def _discard_autosave(self, index):
        editor = self.tab_widget.widget(index)
        path = getattr(editor, "file_path", None)
        if not path: return
        editor._has_autosave = False
        title = self.tab_widget.tabText(index).lstrip("[!] ")
        self.tab_widget.setTabText(index, title)
        self.tab_widget.setTabToolTip(index, "")
        self._clear_autosave(path)
        self._append_console(f"Autosave discarded: {os.path.basename(path)}", "action")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Script name bar
        name_bar = QtWidgets.QHBoxLayout()
        name_bar.addWidget(QtWidgets.QLabel("Active Script:"))
        self.filename_edit = QtWidgets.QLineEdit()
        self.filename_edit.setPlaceholderText("Enter script_name.py here...")
        name_bar.addWidget(self.filename_edit)
        main_layout.addLayout(name_bar)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # ------------------------------------------------------------------
        # Left panel (sidebar)
        # ------------------------------------------------------------------
        left_widget = QtWidgets.QWidget()
        left_widget.setMinimumWidth(180)
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # User selector
        user_layout = QtWidgets.QHBoxLayout()
        self.user_combo = QtWidgets.QComboBox()
        users = []
        try:
            if os.path.exists(BASE_SHARED_PATH):
                users = [n for n in os.listdir(BASE_SHARED_PATH)
                         if os.path.isdir(os.path.join(BASE_SHARED_PATH, n))]
        except Exception:
            pass
        if self.current_user not in users:
            users.insert(0, self.current_user)
        if "all_users" not in users:
            users.append("all_users")
        self.user_combo.addItems(users)
        self.user_combo.setCurrentText(self.current_user)
        self.user_combo.currentTextChanged.connect(self._on_user_changed)
        user_layout.addWidget(QtWidgets.QLabel("User:"))
        user_layout.addWidget(self.user_combo)
        left_layout.addLayout(user_layout)

        # Single search box — filters by name; press Enter to search contents
        search_row = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Filter scripts...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_edit)
        self.search_mode_btn = QtWidgets.QPushButton("Name")
        self.search_mode_btn.setFixedWidth(60)
        self.search_mode_btn.setCheckable(True)
        self.search_mode_btn.setChecked(False)
        self.search_mode_btn.setToolTip("Toggle between filtering by filename or searching inside file contents")
        self.search_mode_btn.clicked.connect(self._on_search_mode_toggled)
        self.search_mode_btn.setStyleSheet("""
            QPushButton { background:#2D2D30; color:#888; border:1px solid #3C3C3C; padding:2px; }
            QPushButton:checked { background:#094771; color:#9CDCFE; border:1px solid #007ACC; }
        """)
        search_row.addWidget(self.search_mode_btn)
        left_layout.addLayout(search_row)

        self.script_list = QtWidgets.QListWidget()
        self.script_list.itemDoubleClicked.connect(self._on_script_double_clicked)
        self.script_list.itemClicked.connect(self._on_script_clicked)
        self.script_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self._on_script_context_menu)
        left_layout.addWidget(self.script_list, 5)

        new_btn = QtWidgets.QPushButton("New Script")
        new_btn.clicked.connect(self._new_script)
        left_layout.addWidget(new_btn)

        # Script Info & Comments — collapsible, collapsed by default
        self.info_group = QtWidgets.QGroupBox("▶  Script Info & Comments")
        info_layout = QtWidgets.QVBoxLayout(self.info_group)
        info_layout.setSpacing(4)
        self.info_group.mousePressEvent = lambda e: self._toggle_group(
            self.info_group, self._info_body
        )
        self._info_body = QtWidgets.QWidget()
        ib_layout = QtWidgets.QVBoxLayout(self._info_body)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setSpacing(4)
        ib_layout.addWidget(QtWidgets.QLabel("Description:"))
        self.desc_edit = QtWidgets.QPlainTextEdit()
        self.desc_edit.setPlaceholderText("Add a description for this script...")
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setStyleSheet("background:#1E1E1E; color:#D4D4D4;")
        ib_layout.addWidget(self.desc_edit)
        save_desc_btn = QtWidgets.QPushButton("Save Description")
        save_desc_btn.clicked.connect(self._save_description)
        ib_layout.addWidget(save_desc_btn)
        ib_layout.addWidget(QtWidgets.QLabel("Comments:"))
        self.comments_list = QtWidgets.QListWidget()
        self.comments_list.setStyleSheet("background:#1E1E1E; color:#D4D4D4;")
        self.comments_list.setMinimumHeight(80)
        self.comments_list.setWordWrap(True)
        ib_layout.addWidget(self.comments_list)
        self.comment_edit = QtWidgets.QLineEdit()
        self.comment_edit.setPlaceholderText("Write a comment...")
        self.comment_edit.setStyleSheet("background:#1E1E1E; color:#D4D4D4;")
        self.comment_edit.returnPressed.connect(self._post_comment)
        ib_layout.addWidget(self.comment_edit)
        comment_btns = QtWidgets.QHBoxLayout()
        post_btn = QtWidgets.QPushButton("Post Comment")
        post_btn.clicked.connect(self._post_comment)
        refresh_meta_btn = QtWidgets.QPushButton("↻ Refresh")
        refresh_meta_btn.setFixedWidth(70)
        refresh_meta_btn.clicked.connect(self._refresh_meta_panel)
        comment_btns.addWidget(post_btn)
        comment_btns.addWidget(refresh_meta_btn)
        ib_layout.addLayout(comment_btns)
        self._info_body.hide()
        info_layout.addWidget(self._info_body)
        left_layout.addWidget(self.info_group)

        # Node Picker — compact, collapsible
        self.node_picker_group = QtWidgets.QGroupBox("▼  Node Picker")
        np_layout = QtWidgets.QVBoxLayout(self.node_picker_group)
        self.node_picker_group.mousePressEvent = lambda e: self._toggle_group(
            self.node_picker_group, self._np_body
        )
        np_layout.setSpacing(3)

        np_search_row = QtWidgets.QHBoxLayout()
        self.node_picker_search = QtWidgets.QLineEdit()
        self.node_picker_search.setPlaceholderText("Filter nodes...")
        self.node_picker_search.textChanged.connect(self._filter_node_picker)
        np_search_row.addWidget(self.node_picker_search)

        # Pipette button
        self.pipette_btn = QtWidgets.QPushButton("Pick")
        self.pipette_btn.setFixedWidth(28)
        self.pipette_btn.setToolTip(
            "Click to start 5s countdown. Select a NEW node in the graph. Click again to cancel."
        )
        self.pipette_btn.clicked.connect(self._activate_pipette)
        np_search_row.addWidget(self.pipette_btn)
        np_layout.addLayout(np_search_row)

        self._np_body = QtWidgets.QWidget()
        np_body_layout = QtWidgets.QVBoxLayout(self._np_body)
        np_body_layout.setContentsMargins(0, 0, 0, 0)
        self.node_picker_list = QtWidgets.QListWidget()
        self.node_picker_list.setMaximumHeight(100)
        np_body_layout.addWidget(self.node_picker_list)
        np_btn_row = QtWidgets.QHBoxLayout()
        refresh_nodes_btn = QtWidgets.QPushButton("Refresh")
        refresh_nodes_btn.setToolTip("Refresh the node list from the current Nuke scene")
        refresh_nodes_btn.clicked.connect(self._populate_node_picker)
        open_knob_btn = QtWidgets.QPushButton("Edit knobChanged")
        open_knob_btn.setToolTip("Open knobChanged for the selected node in the picker")
        open_knob_btn.clicked.connect(self._edit_knobchanged_from_picker)
        np_btn_row.addWidget(refresh_nodes_btn)
        np_btn_row.addWidget(open_knob_btn)
        np_body_layout.addLayout(np_btn_row)
        np_layout.addWidget(self._np_body)
        left_layout.addWidget(self.node_picker_group)

        # History — collapsible
        self.history_group = QtWidgets.QGroupBox("▶  Execution History")
        history_layout = QtWidgets.QVBoxLayout(self.history_group)
        self.history_group.mousePressEvent = lambda e: self._toggle_group(
            self.history_group, self._history_body
        )
        self._history_body = QtWidgets.QWidget()
        hb_layout = QtWidgets.QVBoxLayout(self._history_body)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        self.history_list = QtWidgets.QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_double_clicked)
        hb_layout.addWidget(self.history_list)
        self._history_body.hide()
        history_layout.addWidget(self._history_body)
        left_layout.addWidget(self.history_group)

        # Variables — collapsible
        self.vars_group = QtWidgets.QGroupBox("▶  Session Variables")
        vars_layout = QtWidgets.QVBoxLayout(self.vars_group)
        self.vars_group.mousePressEvent = lambda e: self._toggle_group(
            self.vars_group, self._vars_body
        )
        self._vars_body = QtWidgets.QWidget()
        vb_layout = QtWidgets.QVBoxLayout(self._vars_body)
        vb_layout.setContentsMargins(0, 0, 0, 0)
        self.vars_list = QtWidgets.QListWidget()
        vb_layout.addWidget(self.vars_list)
        self._vars_body.hide()
        vars_layout.addWidget(self._vars_body)
        left_layout.addWidget(self.vars_group)

        help_btn = QtWidgets.QPushButton("Manual")
        help_btn.setMinimumHeight(28)
        help_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        help_btn.setStyleSheet("""
            QPushButton { background:#333; border:1px solid #444; color:#9CDCFE;
                          font-weight:bold; padding:4px 12px; }
            QPushButton:hover { background:#444; border:1px solid #007ACC; }
        """)
        help_btn.clicked.connect(self._show_help_tab)
        left_layout.addWidget(help_btn)

        splitter.addWidget(left_widget)

        # ------------------------------------------------------------------
        # Right panel
        # ------------------------------------------------------------------
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Find & Replace bar
        self.search_bar_widget = QtWidgets.QWidget()
        self.search_bar_widget.hide()
        self.search_bar_widget.setStyleSheet(
            "background-color:#2D2D2D; border-bottom:2px solid #111;"
        )
        sb_vlyt = QtWidgets.QVBoxLayout(self.search_bar_widget)
        sb_vlyt.setContentsMargins(10, 5, 10, 5)
        sb_vlyt.setSpacing(4)

        row1 = QtWidgets.QHBoxLayout()
        self.editor_search_edit = QtWidgets.QLineEdit()
        self.editor_search_edit.setPlaceholderText("Find...")
        self.editor_search_edit.setStyleSheet(
            "background:#3C3C3C; color:#D4D4D4; padding:2px;"
        )
        self.editor_search_edit.textChanged.connect(self._do_editor_search)
        self.editor_search_edit.returnPressed.connect(self._find_next)

        find_prev_btn = QtWidgets.QPushButton("Prev")
        find_prev_btn.setFixedWidth(50)
        find_prev_btn.clicked.connect(self._find_prev)
        find_next_btn = QtWidgets.QPushButton("Next")
        find_next_btn.setFixedWidth(50)
        find_next_btn.clicked.connect(self._find_next)
        close_sb_btn = QtWidgets.QPushButton("✕")
        close_sb_btn.setFixedWidth(25)
        close_sb_btn.setStyleSheet("border:none; color:#888; font-size:14px;")
        close_sb_btn.clicked.connect(self.search_bar_widget.hide)

        row1.addWidget(QtWidgets.QLabel("Find:"))
        row1.addWidget(self.editor_search_edit)
        row1.addWidget(find_prev_btn)
        row1.addWidget(find_next_btn)
        row1.addWidget(close_sb_btn)

        row2 = QtWidgets.QHBoxLayout()
        self.editor_replace_edit = QtWidgets.QLineEdit()
        self.editor_replace_edit.setPlaceholderText("Replace with...")
        self.editor_replace_edit.setStyleSheet(
            "background:#3C3C3C; color:#D4D4D4; padding:2px;"
        )
        replace_btn = QtWidgets.QPushButton("Replace")
        replace_btn.setFixedWidth(70)
        replace_btn.clicked.connect(self._replace_next)
        replace_all_btn = QtWidgets.QPushButton("All")
        replace_all_btn.setFixedWidth(40)
        replace_all_btn.clicked.connect(self._replace_all)
        row2.addWidget(QtWidgets.QLabel("Replace:"))
        row2.addWidget(self.editor_replace_edit)
        row2.addWidget(replace_btn)
        row2.addWidget(replace_all_btn)
        row2.addSpacing(29)

        sb_vlyt.addLayout(row1)
        sb_vlyt.addLayout(row2)
        right_layout.insertWidget(0, self.search_bar_widget)

        # Editor tabs + console splitter
        vert_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(
            self._on_tab_bar_context_menu
        )
        vert_splitter.addWidget(self.tab_widget)

        # Console
        console_container = QtWidgets.QWidget()
        console_layout = QtWidgets.QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 2, 0, 0)

        console_header = QtWidgets.QHBoxLayout()
        self.status_light = QtWidgets.QLabel("●")
        self.status_light.setStyleSheet("color:#555; font-size:18px; margin-right:5px;")
        console_header.addWidget(self.status_light)
        console_header.addWidget(QtWidgets.QLabel("Console:"))
        console_header.addStretch()
        hint = QtWidgets.QLabel("Ctrl+F: Find  |  Ctrl+G: Go to line  |  Ctrl+Shift+T: Reopen closed tab")
        hint.setStyleSheet("color:#555; font-style:italic; font-size:10px;")
        console_header.addWidget(hint)
        console_header.addStretch()
        console_header.addWidget(QtWidgets.QLabel("View:"))
        self.console_mode = QtWidgets.QComboBox()
        self.console_mode.addItems(["All", "Errors Only", "Actions/Info"])
        self.console_mode.setFixedWidth(120)
        self.console_mode.currentIndexChanged.connect(self._apply_console_filter)
        console_header.addWidget(self.console_mode)
        console_layout.addLayout(console_header)

        self.console_output = QtWidgets.QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background:#1A1A1A; color:#D4D4D4;")
        self.console_output.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        console_layout.addWidget(self.console_output)

        vert_splitter.addWidget(console_container)
        vert_splitter.setStretchFactor(0, 4)
        vert_splitter.setStretchFactor(1, 1)
        # Set initial sizes explicitly so editor gets most of the space
        QtCore.QTimer.singleShot(0, lambda: vert_splitter.setSizes([600, 150]))
        vert_splitter.setCollapsible(0, False)
        vert_splitter.setCollapsible(1, False)
        right_layout.addWidget(vert_splitter, 1)

        # ------------------------------------------------------------------
        # Bottom button row — trimmed to essentials + "Nuke ▾" dropdown
        # ------------------------------------------------------------------
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(4, 6, 4, 4)

        def _add_btn(label, slot, tip=""):
            b = QtWidgets.QPushButton(label)
            if tip: b.setToolTip(tip)
            b.clicked.connect(slot)
            btn_layout.addWidget(b)
            return b

        _add_btn("Save",             self.save_script,              "Save active tab  (Ctrl+S)")
        _add_btn("Save As...",       self.save_script_as,           "Save as a new file")
        _add_btn("Run",              self.execute_code,             "Run entire script  (Ctrl+Enter)")
        _add_btn("Run Selection",    self.execute_selection,        "Run selected text  (Ctrl+Shift+Enter)")
        _add_btn("Run on Nodes",     self.execute_on_selected_nodes,"Wrap script in for-loop over selected nodes")
        _add_btn("Edit knobChanged", self.edit_knobchanged_on_selected,
                 "Open knobChanged for selected node(s). If nothing selected, opens Node Picker.")
        _add_btn("Refresh Vars",     self.refresh_variables,        "Refresh Session Variables panel")

        # Nuke dropdown
        nuke_menu = QtWidgets.QMenu(self)
        nuke_menu.addSeparator()
        nuke_menu.addAction("→ Nuke Script Editor",
                            self._import_to_nuke_script_editor)
        nuke_menu.addSeparator()
        nuke_menu.addAction("Snippet Manager",
                            self._open_snippet_manager)

        nuke_btn = QtWidgets.QPushButton("Nuke ▾")
        nuke_btn.setStyleSheet("""
            QPushButton { background:#2D2D30; color:#9CDCFE;
                          border:1px solid #3C3C3C; padding:4px 8px; }
            QPushButton:hover { background:#3C3C3C; }
        """)
        nuke_btn.setMenu(nuke_menu)
        btn_layout.addWidget(nuke_btn)

        # Refresh console dropdown
        refresh_menu = QtWidgets.QMenu(self)
        refresh_menu.addAction("Soft Refresh (keep errors/actions)",
                               self._console_soft_refresh)
        refresh_menu.addAction("Hard Refresh (clear console)",
                               self._console_hard_refresh)
        refresh_menu.addAction("Full Reset (console + filters)",
                               self._console_full_reset)

        refresh_console_btn = QtWidgets.QPushButton("Console ▾")
        refresh_console_btn.setStyleSheet("""
            QPushButton { background:#2D2D30; color:#9CDCFE;
                          border:1px solid #3C3C3C; padding:4px 8px; }
            QPushButton:hover { background:#3C3C3C; }
        """)
        refresh_console_btn.setMenu(refresh_menu)
        btn_layout.addWidget(refresh_console_btn)
        btn_layout.addStretch(1)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_container)
        splitter.setStretchFactor(1, 1)

        # Status bar
        status_row = QtWidgets.QHBoxLayout()
        self.line_col_label = QtWidgets.QLabel("Ln 1, Col 1")
        self.line_col_label.setStyleSheet(
            "font-size:10px; color:#888; padding-right:10px;"
        )
        self.status_bar = QtWidgets.QLabel()
        self.status_bar.setStyleSheet(
            "font-size:10px; color:#888; border-top:1px solid #333;"
        )
        status_row.addWidget(self.line_col_label)
        status_row.addWidget(self.status_bar, 1)
        main_layout.addLayout(status_row)

        # Shortcuts
        shortcuts = [
            ("Ctrl+F",           self._show_search_bar),
            ("Esc",              self.search_bar_widget.hide),
            ("Ctrl+S",           self.save_script),
            ("Ctrl+Return",      self.execute_code),
            ("Ctrl+Shift+Return", self.execute_selection),
            ("Ctrl+G",           self._go_to_line),
            ("Ctrl+Shift+T",     self._reopen_last_closed_tab),
        ]
        for key, slot in shortcuts:
            sc = UniversalShortcut(QtGui.QKeySequence(key), self)
            sc.activated.connect(slot)

        self._populate_node_picker()

        # Always open with an Untitled tab — session restore adds its tabs after
        self._new_tab("Untitled")

    # ------------------------------------------------------------------
    # Script Info & Comments (Meta)
    # ------------------------------------------------------------------

    def _update_info_group_title(self):
        """Show 📝/💬 indicators. 💬 N = unread, 💬 = all read."""
        if not hasattr(self, "info_group") or not self._current_meta_script: return
        try:
            scripts_dir = os.path.dirname(self._current_meta_script)
            meta = read_meta(scripts_dir, self._current_meta_script)
            comments = meta.get("comments", [])
            has_desc = bool(meta.get("description", "").strip())

            # Count unread: comments newer than last_read timestamp for this user
            last_read_str = meta.get("last_read", {}).get(self.current_user, "")
            if last_read_str:
                try:
                    last_read_dt = datetime.datetime.strptime(last_read_str, "%Y-%m-%d %H:%M")
                    unread = sum(
                        1 for c in comments
                        if datetime.datetime.strptime(
                            c.get("timestamp", "1970-01-01 00:00"), "%Y-%m-%d %H:%M"
                        ) > last_read_dt
                        and c.get("user") != self.current_user
                    )
                except Exception:
                    unread = 0
            else:
                # Never read — all comments from others are unread
                unread = sum(1 for c in comments if c.get("user") != self.current_user)

            parts = []
            if has_desc: parts.append("📝")
            if unread:
                parts.append(f"💬 +{unread}")   # unread indicator
            elif comments:
                parts.append("💬")              # has comments, all read
            suffix = "  " + " ".join(parts) if parts else ""
            arrow = "▼" if self._info_body.isVisible() else "▶"
            self.info_group.setTitle(f"{arrow}  Script Info & Comments{suffix}")
        except Exception: pass

    def _mark_comments_read(self):
        """Stamp current time as last_read for this user on the current script."""
        if not self._current_meta_script: return
        try:
            scripts_dir = os.path.dirname(self._current_meta_script)
            meta = read_meta(scripts_dir, self._current_meta_script)
            last_read = meta.get("last_read", {})
            last_read[self.current_user] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            meta["last_read"] = last_read
            write_meta(scripts_dir, self._current_meta_script, meta)
        except Exception: pass

    def _on_script_clicked(self, item):
        path = item.data(QtCore.Qt.UserRole)
        if not path: return
        self._current_meta_script = path
        scripts_dir = os.path.dirname(path)
        meta = read_meta(scripts_dir, path)
        self.desc_edit.setPlainText(meta.get("description", ""))
        self.comments_list.clear()
        for c in meta.get("comments", []):
            self.comments_list.addItem(
                f"[{c.get('timestamp','')}] {c.get('user','?')}: {c.get('text','')}"
            )
        self.comments_list.scrollToBottom()
        # Mark as read only if the panel is expanded (user can actually see comments)
        if self._info_body.isVisible():
            self._mark_comments_read()
        self._update_info_group_title()

    def _refresh_meta_panel(self):
        if not self._current_meta_script: return
        item = self.script_list.currentItem()
        if item:
            self._on_script_clicked(item)
            self._mark_comments_read()
            self._update_info_group_title()

    def _save_description(self):
        if not self._current_meta_script:
            self._append_console("Select a script first.", "error"); return
        scripts_dir = os.path.dirname(self._current_meta_script)
        meta = read_meta(scripts_dir, self._current_meta_script)
        meta["description"] = self.desc_edit.toPlainText().strip()
        write_meta(scripts_dir, self._current_meta_script, meta)
        self._update_info_group_title()
        self._append_console(f"Description saved: {os.path.basename(self._current_meta_script)}", "action")

    def _post_comment(self):
        if not self._current_meta_script:
            self._append_console("Select a script first.", "error"); return
        text = self.comment_edit.text().strip()
        if not text: return
        scripts_dir = os.path.dirname(self._current_meta_script)
        meta = read_meta(scripts_dir, self._current_meta_script)
        comments = meta.get("comments", [])
        comments.append({
            "user":      self.current_user,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text":      text,
        })
        meta["comments"] = comments[-50:]
        write_meta(scripts_dir, self._current_meta_script, meta)
        self.comment_edit.clear()
        self._on_script_clicked(self.script_list.currentItem())
        self._append_console(f"Comment posted: {os.path.basename(self._current_meta_script)}", "action")

    # ------------------------------------------------------------------
    # Snippets
    # ------------------------------------------------------------------

    def _get_all_snippets(self):
        """Return merged list: builtins + shared + personal."""
        snippets = list(BUILTIN_SNIPPETS)
        sp = shared_snippets_path()
        if os.path.exists(sp):
            try:
                with open(sp, "r") as f:
                    snippets += json.load(f)
            except Exception:
                pass
        pp = personal_snippets_path(self.current_repo_path, self.current_user)
        if os.path.exists(pp):
            try:
                with open(pp, "r") as f:
                    snippets += json.load(f)
            except Exception:
                pass
        return snippets

    def _save_personal_snippets(self, snippets):
        pp = personal_snippets_path(self.current_repo_path, self.current_user)
        # Safety: only ever write to a file ending in _snippets.json
        if not pp.endswith("_snippets.json"):
            self._append_console("Snippet save aborted: unexpected file path.", "error")
            return
        try:
            with open(pp, "w") as f:
                json.dump(snippets, f, indent=4)
        except Exception as e:
            self._append_console(f"Failed to save snippets: {e}", "error")

    def _save_shared_snippets(self, snippets):
        sp = shared_snippets_path()
        if not sp.endswith("_snippets.json"):
            self._append_console("Snippet save aborted: unexpected file path.", "error")
            return
        try:
            with open(sp, "w") as f:
                json.dump(snippets, f, indent=4)
        except Exception as e:
            self._append_console(f"Failed to save shared snippets: {e}", "error")

    def _load_personal_snippets(self):
        pp = personal_snippets_path(self.current_repo_path, self.current_user)
        if not os.path.exists(pp):
            return []
        try:
            with open(pp, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _load_shared_snippets(self):
        sp = shared_snippets_path()
        if not os.path.exists(sp):
            return []
        try:
            with open(sp, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _open_snippet_manager(self):
        dlg = SnippetManagerDialog(self)
        dlg.exec_()

    # ------------------------------------------------------------------
    # Node Picker
    # ------------------------------------------------------------------

    def _populate_node_picker(self):
        self.node_picker_list.clear()
        if not nuke:
            self.node_picker_list.addItem("(Nuke not available)")
            return
        if not self._pipette_active:
            try:
                sel = nuke.selectedNodes()
                if sel: self._last_nuke_selection = sel
            except Exception: pass
        for node in sorted(nuke.allNodes(), key=lambda n: n.name()):
            self.node_picker_list.addItem(node.name())

    def _filter_node_picker(self, text):
        for i in range(self.node_picker_list.count()):
            item = self.node_picker_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _edit_knobchanged_from_picker(self):
        item = self.node_picker_list.currentItem()
        if not item or not nuke:
            self._append_console("Select a node from the picker first.", "error")
            return
        node = nuke.toNode(item.text())
        if not node:
            self._append_console(f"Node '{item.text()}' not found.", "error")
            return
        self._open_knobchanged_for_node(node)

    # ------------------------------------------------------------------
    # Pipette — pick selected node immediately, or poll for 5 seconds
    # ------------------------------------------------------------------

    def _activate_pipette(self):
        if not nuke:
            self._append_console("Nuke API not available.", "error")
            return

        if self._pipette_active:
            self._pipette_timer.stop()
            self._pipette_reset_btn()
            self._pipette_active = False
            self._pipette_ignore_nodes = set()
            self._append_console("Pipette: cancelled.", "info")
            return

        # Snapshot nodes currently selected so we can ignore them.
        # The user must click a node AFTER the countdown starts.
        try:
            self._pipette_ignore_nodes = {
                n.name() for n in (nuke.selectedNodes() if nuke else [])
            }
        except Exception:
            self._pipette_ignore_nodes = set()

        self._last_nuke_selection = []   # also clear Edit-knobChanged cache
        self._pipette_active = True
        self._pipette_countdown = 5
        self.pipette_btn.setStyleSheet("background:#CCA700; color:#000;")
        self.pipette_btn.setText(str(self._pipette_countdown))
        self._pipette_timer = QtCore.QTimer(self)
        self._pipette_timer.setInterval(1000)
        self._pipette_timer.timeout.connect(self._pipette_poll)
        self._pipette_timer.start()
        self._append_console(
            "Pipette: click a different node in Nuke within 5 seconds...", "action"
        )

    def _pipette_poll(self):
        if not self._pipette_active:
            return
        try:
            raw = nuke.selectedNodes() if nuke else []
        except Exception:
            raw = []
        # Ignore any nodes that were already selected when countdown started
        sel = [n for n in raw if n.name() not in self._pipette_ignore_nodes]
        if sel:
            self._pipette_timer.stop()
            self._pipette_reset_btn()
            self._pipette_active = False
            self._pipette_pick_node(sel[0])
            return
        self._pipette_countdown -= 1
        self.pipette_btn.setText(str(self._pipette_countdown))
        if self._pipette_countdown <= 0:
            self._pipette_timer.stop()
            self._pipette_reset_btn()
            self._pipette_active = False
            self._append_console("Pipette: timed out, no node selected.", "info")

    def _pipette_reset_btn(self):
        self.pipette_btn.setStyleSheet("")
        self.pipette_btn.setText("Pick")

    def _pipette_pick_node(self, node):
        # Highlight it in the picker list
        self._populate_node_picker()
        for i in range(self.node_picker_list.count()):
            if self.node_picker_list.item(i).text() == node.name():
                self.node_picker_list.setCurrentRow(i)
                break
        self._append_console(f"Pipette: picked '{node.name()}'.", "action")

    # ------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------

    def _console_soft_refresh(self):
        doc = self.console_output.document()
        lines = []
        block = doc.firstBlock()
        while block.isValid():
            if block.userState() in (1, 2):
                lines.append((block.text(), block.userState()))
            block = block.next()
        self.console_output.clear()
        for text, state in lines:
            self._append_console(text, "error" if state == 1 else "action")
        self._append_console("Console soft-refreshed.", "action")

    def _console_hard_refresh(self):
        self.console_output.clear()
        self._append_console("Console cleared.", "action")

    def _console_full_reset(self):
        self.console_output.clear()
        self.console_mode.setCurrentText("All")
        self._append_console("Console fully reset.", "action")

    def _append_console(self, text, msg_type="info"):
        if not text: return
        self.console_output.moveCursor(QtGui.QTextCursor.End)
        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QColor(
            {"info": "#D4D4D4", "error": "#F44747", "action": "#9CDCFE"}.get(msg_type, "#D4D4D4")
        ))
        self.console_output.setCurrentCharFormat(fmt)
        self.console_output.insertPlainText(text + "\n")
        self.console_output.document().lastBlock().setUserState(
            1 if msg_type == "error" else 2 if msg_type == "action" else 0
        )
        self.console_output.ensureCursorVisible()
        self._apply_console_filter()

    def _apply_console_filter(self):
        mode = self.console_mode.currentText()
        self.console_output.blockSignals(True)
        block = self.console_output.document().begin()
        while block.isValid():
            s = block.userState()
            block.setVisible(
                True if mode == "All"
                else s == 1 if mode == "Errors Only"
                else s in (0, 2)
            )
            block = block.next()
        self.console_output.blockSignals(False)
        self.console_output.viewport().update()

    # ------------------------------------------------------------------
    # Help tab
    # ------------------------------------------------------------------

    def _show_help_tab(self):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Manual":
                self.tab_widget.setCurrentIndex(i); return

        manual_text = """
# ======================================================================
# NUKE CODE BRIDGE v0.15 - MANUAL
# ======================================================================
# A multi-user, network-based Python & Blink development environment
# for Foundry Nuke. Supports shared scripts, snippets, and node editing.
# ======================================================================

[ ⌨ KEYBOARD SHORTCUTS ]
------------------------------------------------------------------------
  Ctrl + S              : Save active tab.
  Ctrl + Enter          : Run entire script.
  Ctrl + Shift + Enter  : Run selected text.
  Ctrl + F              : Open Find & Replace bar.
  Ctrl + G              : Go to line number.
  Ctrl + Shift + T      : Reopen last closed tab.
  Esc                   : Close Find & Replace bar.
  Ctrl + Mouse Wheel    : Zoom editor text in/out.
  Ctrl + 0              : Reset zoom to default.
  Tab                   : Indent selection OR expand snippet trigger.
  Shift + Tab           : Unindent selection.


[ 📁 FILE MANAGEMENT ]
------------------------------------------------------------------------
  Scripts save to:   {BASE_SHARED_PATH}/{username}/scripts/
  Snippets save to:  {BASE_SHARED_PATH}/{username}/{username}_snippets.json
  Shared snippets:   {BASE_SHARED_PATH}/shared_snippets.json

  BACKUPS:
  Every manual save creates a .bak in scripts/_backups/{scriptname}/.
  The last 3 backups are kept automatically.

  CRASH RECOVERY:
  Every 5 minutes, unsaved changes are written to a .autosave file
  next to the script. On next open, if the autosave is newer than the
  saved file by more than 30 seconds, you are offered to restore it.
  Autosave files are deleted on normal close — they only survive a crash.


[ 💬 SCRIPT INFO & COMMENTS ]
------------------------------------------------------------------------
  Click a script to load its info. Expand the header to see/edit it.
  Collapsed header shows indicators: 📝 = description, 💬 N = N comments.
  - Save Description : documents what the script does.
  - Post Comment     : leave notes for the team (Enter or click Post).
  - Refresh          : reload from disk.
  Stored in scripts/_meta/. Last 50 comments per script kept.


[ 🔍 SEARCH ]
------------------------------------------------------------------------
  The sidebar search box has two modes (toggle with the Name/Contents
  button next to it):

  NAME mode     : Filters the script list live as you type by filename.
  CONTENTS mode : Searches inside all script files as you type.
                  Matching files shown in blue with ⬡ prefix.
                  Opening a file in Contents mode auto-fills the
                  Find bar with your search term.


[ ⚡ SNIPPETS ]
------------------------------------------------------------------------
  Snippets are reusable code blocks triggered by a short keyword.

  HOW TO USE:
  1. Type a trigger word in the editor (e.g. "fornode").
  2. The word gets an amber highlight when a snippet is ready.
  3. Press Tab to expand it. The cursor jumps to $CURSOR$ position.

  MANAGING SNIPPETS:
  Open via Nuke ▾ → Snippet Manager.
  - Personal pool : only visible to you.
  - Shared pool   : visible to the whole team.
  - Built-in      : always available, read-only.

  BUILT-IN TRIGGERS:
  fornode  → for node in nuke.selectedNodes(): ...
  ifnuke   → if nuke: ...
  tryex    → try/except block
  defn     → def function(): ...
  blink    → Blink kernel template
  blinkp   → Blink param block

  Move a personal snippet to shared via "→ Move to Shared" in manager.


[ 🎯 NUKE FEATURES ]
------------------------------------------------------------------------
  EDIT KNOBCHANGED:
  Select one or more nodes in the node graph, then click
  "Edit knobChanged". Each node opens in its own tab.
  If nothing is selected, the Node Picker opens in the sidebar.
  Save writes the code back to the node's knobChanged knob.
  If the node is deleted, Save As lets you keep the code as a file.

  NODE PICKER:
  Browse and filter all nodes in the current Nuke session.
  💉 Pipette: grabs the currently selected node, or waits 5 seconds
  for you to click one in the node graph.

  RUN ON SELECTED NODES:
  Wraps your script in "for node in nuke.selectedNodes():" and runs it.
  Use the variable "node" in your script to refer to each node.

  → NUKE SCRIPT EDITOR:
  Sends the current tab's code to Nuke's built-in Script Editor.
  The Script Editor panel must be open in your Nuke layout.


[ 🚦 CONSOLE ]
------------------------------------------------------------------------
  ● GREY   : Idle — waiting for code.
  ● YELLOW : Executing.
  ● GREEN  : Success.
  ● RED    : Error — switch View to "Errors Only" to isolate it.

  FILTER MODES (View dropdown):
  All          : Shows everything.
  Errors Only  : Hides everything except Python tracebacks.
  Actions/Info : Shows action messages and print() output only.

  Console ▾ menu:
  Soft Refresh : Keeps errors and actions, clears info messages.
  Hard Refresh : Clears everything.
  Full Reset   : Clears everything and resets the filter to "All".


[ 💡 TIPS ]
------------------------------------------------------------------------
  - Right-click any tab header: Duplicate, Close, Reopen Last Closed.
  - History and Variables panels are collapsed by default.
    Click the group header (▶) to expand them.
  - Ln/Col shown bottom-left. Turns amber when on a snippet trigger.
  - Asterisk (*) on a tab = unsaved changes.
  - Session recovery: Untitled tabs with content are restored on reopen.
  - The tool only runs while open — no background processes in Nuke.
# ======================================================================
"""
        help_editor = CodeEditor()
        help_editor.setPlainText(manual_text.strip())
        help_editor.setReadOnly(True)
        help_editor.setStyleSheet(
            "background:#1A1A1A; color:#9CDCFE; border-left:4px solid #007ACC;"
        )
        idx = self.tab_widget.addTab(help_editor, "Manual")
        self.tab_widget.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _run_code_block(self, code, label="script"):
        self._add_to_history(code)
        self.console_output.clear()
        self.status_light.setStyleSheet("color:#CCA700; font-size:18px;")
        self._append_console(f">>> Executing {label}...", "action")

        redirector = StreamRedirector(self.console_output)
        success = True
        try:
            with redirector:
                self._exec_in_namespace(code)
        except Exception:
            success = False
            etype, value, tb = sys.exc_info()
            self._append_console("-" * 50, "error")
            self._append_console("PYTHON ERROR:", "error")
            self._append_console("".join(traceback.format_exception(etype, value, tb)), "error")
            self._append_console("-" * 50, "error")
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        self.status_light.setStyleSheet(
            "color:#6A9955; font-size:18px;" if success else "color:#F44747; font-size:18px;"
        )
        if success:
            self._append_console(f">>> SUCCESS: {label.capitalize()} finished.", "info")
        self._force_raise()

    def execute_code(self):
        editor = self.get_current_editor()
        if not editor: return
        code = editor.toPlainText()
        if not code.strip(): return
        if SHOW_RUN_CONFIRMATION:
            msg = "Execute this script?"
            if nuke:
                if not nuke.ask(msg): return
            else:
                if QtWidgets.QMessageBox.question(self, "Run?", msg) != QtWidgets.QMessageBox.Yes: return
        self._run_code_block(code, "script")

    def execute_selection(self):
        editor = self.get_current_editor()
        if not editor: return
        selected = editor.textCursor().selectedText()
        code = (selected.replace("\u2029", "\n").replace("\u2028", "\n")
                if selected.strip() else editor.toPlainText())
        self._run_code_block(code, "selection")

    def execute_on_selected_nodes(self):
        if not nuke:
            self._append_console("Nuke API not available.", "error"); return
        editor = self.get_current_editor()
        if not editor: return
        inner = editor.toPlainText()
        if not inner.strip(): return
        indented = "\n".join("    " + line for line in inner.splitlines())
        self._run_code_block(f"for node in nuke.selectedNodes():\n{indented}\n",
                             "script on selected nodes")

    def _import_to_nuke_script_editor(self):
        """Send current code to Nuke's Script Editor input field.

        Tries three approaches in order:
        1. nuke.getPaneFor() with the known panel ID (Nuke 15/17)
        2. QApplication widget tree scan by objectName
        3. Clipboard fallback with clear instructions
        """
        if not nuke:
            self._append_console("Nuke API not available.", "error"); return
        editor = self.get_current_editor()
        if not editor: return
        code = editor.toPlainText()
        sent = False

        # Find the Script Editor panel by its known objectName, then find
        # its writable QTextEdit child (confirmed via widget inspection in Nuke 15/17)
        try:
            for widget in QtWidgets.QApplication.allWidgets():
                if widget.objectName() in (
                    "uk.co.thefoundry.scripteditor.1",
                    "uk.co.thefoundry.scripteditor.2",
                ):
                    for child in widget.findChildren(QtWidgets.QPlainTextEdit):
                        if not child.isReadOnly():
                            child.setPlainText(code)
                            self._append_console(
                                "Code sent to Nuke Script Editor.", "action"
                            )
                            sent = True
                            break
                if sent:
                    break
        except Exception as e:
            self._append_console(f"Script Editor error: {e}", "error")

        # Approach 3: clipboard fallback
        if not sent:
            QtWidgets.QApplication.clipboard().setText(code)
            self._append_console(
                "Script Editor not found or not open. "
                "Code copied to clipboard — open the Script Editor and paste (Ctrl+V).",
                "action"
            )

    # ------------------------------------------------------------------
    # knobChanged editing
    # ------------------------------------------------------------------

    def _open_knobchanged_for_node(self, node):
        knob = node.knob("knobChanged")
        existing_code = knob.value() if knob else ""
        tab_title = f"knobChanged: {node.name()}"
        editor = self._create_editor(existing_code, title=tab_title,
                                     file_path=None, knobchanged_node=node)
        idx = self.tab_widget.addTab(editor, tab_title)
        self.tab_widget.setCurrentIndex(idx)
        self.filename_edit.setText(tab_title)

    def edit_knobchanged_on_selected(self):
        """Smart: opens selected nodes directly, or opens Node Picker if none selected."""
        if not nuke:
            self._append_console("Nuke API not available.", "error"); return
        sel = self._get_nuke_selected_nodes()
        if sel:
            for node in sel:
                self._open_knobchanged_for_node(node)
        else:
            self.node_picker_group.setTitle("▼  Node Picker")
            self._np_body.setVisible(True)
            self._populate_node_picker()
            self._append_console(
                "No node selected — pick one from the Node Picker in the sidebar.", "action"
            )

    # ------------------------------------------------------------------
    # Dirty indicator
    # ------------------------------------------------------------------

    def _on_editor_modified(self):
        editor = self.sender()
        idx = self.tab_widget.indexOf(editor)
        if idx == -1: return
        title = self.tab_widget.tabText(idx)
        if not title.endswith("*"):
            self.tab_widget.setTabText(idx, title + "*")

    def _clear_dirty_flag(self, editor):
        idx = self.tab_widget.indexOf(editor)
        if idx == -1: return
        title = self.tab_widget.tabText(idx)
        if title.endswith("*"):
            self.tab_widget.setTabText(idx, title[:-1])

    def _on_editor_zoom_changed(self, zoom_level):
        self.global_zoom = zoom_level

    # ------------------------------------------------------------------
    # Script list
    # ------------------------------------------------------------------

    def _on_user_changed(self, user):
        self.current_repo_path = (
            BASE_SHARED_PATH if USE_SINGLE_SHARED_FOLDER or user == "all_users"
            else os.path.join(BASE_SHARED_PATH, user)
        )
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
                    fp = os.path.join(BASE_SHARED_PATH, f)
                    if os.path.isfile(fp) and f.lower().endswith(".py"):
                        items.append((f, fp))
            except Exception as e:
                self._append_console(f"Failed to list scripts: {e}")
        elif self.user_combo.currentText() == "all_users":
            for root, _, files in os.walk(BASE_SHARED_PATH):
                for f in files:
                    if f.lower().endswith(".py"):
                        items.append((f, os.path.join(root, f)))
        else:
            # Look in both user root (legacy) and scripts/ subfolder (new)
            search_dirs = [self.current_repo_path,
                           os.path.join(self.current_repo_path, "scripts")]
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    try:
                        for f in os.listdir(search_dir):
                            fp = os.path.join(search_dir, f)
                            if os.path.isfile(fp) and f.lower().endswith(".py"):
                                # Avoid duplicates if scripts/ doesn't exist yet
                                if fp not in [x[1] for x in items]:
                                    items.append((f, fp))
                    except Exception as e:
                        self._append_console(f"Failed to list scripts: {e}")

        for name, full_path in sorted(items, key=lambda x: x[0].lower()):
            if search and search not in name.lower():
                continue
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, full_path)
            self.script_list.addItem(item)

        self._update_status_bar()

    def _on_script_double_clicked(self, item):
        self._open_script(item.data(QtCore.Qt.UserRole))

    def _on_script_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)
        if not item: return
        path = item.data(QtCore.Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#2D2D2D; color:#D4D4D4; border:1px solid #454545;
                    padding:4px; font-size:12px; min-width:180px; }
            QMenu::item { padding:6px 30px 6px 25px; border-radius:2px; }
            QMenu::item:selected { background:#094771; color:white; }
            QMenu::separator { height:1px; background:#454545; margin:4px 8px; }
        """)
        menu.addAction("Open Folder Location", lambda: self._open_folder(path))
        menu.addSeparator()
        menu.addAction("Delete Script", lambda: self._delete_script(path))
        menu.exec_(list_widget.mapToGlobal(pos))

    def _open_folder(self, path):
        folder = os.path.dirname(path)
        try:
            if sys.platform.startswith("win"): os.startfile(folder)
            elif sys.platform == "darwin": os.system(f'open "{folder}"')
            else: os.system(f'xdg-open "{folder}"')
        except Exception as e:
            self._append_console(f"Failed to open folder: {e}")

    def _delete_script(self, path):
        if not os.path.exists(path): return
        msg = f"Are you sure you want to delete:\n\n{os.path.basename(path)}"
        if nuke:
            if not nuke.ask(msg): return
        else:
            if QtWidgets.QMessageBox.question(self, "Delete Script", msg) != QtWidgets.QMessageBox.Yes: return
        try:
            os.remove(path)
        except Exception as e:
            self._append_console(f"Failed to delete script: {e}")
        self._refresh_script_list()

    def _open_script(self, path):
        if not os.path.exists(path):
            self._append_console(f"Script not found: {path}"); return

        # If already open in a tab, just switch to it
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if getattr(editor, "file_path", None) == path:
                self.tab_widget.setCurrentIndex(i)
                self._append_console(f"Already open: {os.path.basename(path)}", "action")
                return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self._append_console(f"Failed to open: {e}"); return
        title = os.path.basename(path)
        editor = self._create_editor(content=content, title=title, file_path=path)
        idx = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(idx)
        self.filename_edit.setText(title)
        self._clear_dirty_flag(editor)
        self._check_autosave_on_open(path, editor)
        self._append_console(f"Opened: {path}")

        # If we're in Contents search mode, pre-fill and open the Find bar
        if self.search_mode_btn.isChecked():
            term = self.search_edit.text().strip()
            if term:
                self.editor_search_edit.setText(term)
                self.search_bar_widget.show()
                self._find_next()

    def _new_script(self):
        self._new_tab("Untitled")
        self.filename_edit.clear()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _get_user_save_folder(self):
        user = self.user_combo.currentText()
        if user == "all_users":
            user = self.current_user
        user_folder = os.path.join(BASE_SHARED_PATH, user)
        ensure_directory(user_folder)
        return user_scripts_folder(user_folder)

    def save_script(self):
        editor = self.get_current_editor()
        if not editor: return

        # Gate 1: knobChanged tab
        tab_title = self.tab_widget.tabText(self.tab_widget.currentIndex()).rstrip("*")
        is_knob_tab = (
            getattr(editor, "_editing_knobchanged_node", None) is not None
            or getattr(editor, "_was_knobchanged_recovered", False)
            or tab_title.startswith("knobChanged:")
        )
        if is_knob_tab:
            node = getattr(editor, "_editing_knobchanged_node", None)
            if node is None and nuke:
                try:
                    node = nuke.toNode(tab_title.replace("knobChanged:", "").strip())
                    if node:
                        editor._editing_knobchanged_node = node
                except Exception:
                    node = None
            if node and nuke and node in nuke.allNodes():
                node.knob("knobChanged").setValue(editor.toPlainText())
                self._append_console(
                    f"knobChanged on '{node.name()}' updated successfully.", "action"
                )
                self._clear_dirty_flag(editor)
            else:
                self._append_console(
                    "SAVE FAILED: The linked node is no longer available. "
                    "Use 'Save As' to keep this code as a file.", "error"
                )
                QtWidgets.QMessageBox.warning(
                    self, "Node Not Available",
                    "The node linked to this tab no longer exists in the scene.\n\n"
                    "Use 'Save As' to keep your code as a .py file."
                )
            return

        # Gate 2: existing file
        code = editor.toPlainText()
        path = getattr(editor, "file_path", None)
        if path:
            if CONFIRM_OVERWRITE:
                msg = f"Overwrite '{os.path.basename(path)}' with your changes?"
                if nuke:
                    if not nuke.ask(msg): return
                else:
                    if QtWidgets.QMessageBox.question(self, "Overwrite?", msg) != QtWidgets.QMessageBox.Yes: return
            self._save_to_path(path, code)
            self._clear_dirty_flag(editor)
            self._clear_autosave(path)
            return

        # Gate 3: new untitled
        file_name = self.filename_edit.text().strip()
        if not file_name:
            self._append_console(
                "ERROR: Enter a filename in the top bar before saving.", "error"
            ); return
        if not file_name.lower().endswith(".py"):
            file_name += ".py"
        full_path = os.path.join(self._get_user_save_folder(), file_name)
        self._save_to_path(full_path, code)
        editor.file_path = full_path
        self.tab_widget.setTabText(
            self.tab_widget.currentIndex(), os.path.basename(full_path)
        )
        self._clear_dirty_flag(editor)
        self._refresh_script_list()

    def save_script_as(self):
        editor = self.get_current_editor()
        if not editor: return
        code = editor.toPlainText()
        dialog = QtWidgets.QFileDialog(self, "Save Script As",
                                       self._get_user_save_folder())
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setNameFilter("Python Files (*.py)")
        dialog.setDefaultSuffix("py")
        if dialog.exec_() != QtWidgets.QFileDialog.Accepted: return
        path = dialog.selectedFiles()[0]
        ensure_directory(os.path.dirname(path))
        self._save_to_path(path, code)
        editor.file_path = path
        editor._editing_knobchanged_node = None
        self.tab_widget.setTabText(
            self.tab_widget.currentIndex(), os.path.basename(path)
        )
        self.filename_edit.setText(os.path.basename(path))
        self._clear_dirty_flag(editor)
        self._clear_autosave(path)
        self._refresh_script_list()

    def _save_to_path(self, path, code):
        if ENABLE_BACKUPS and os.path.exists(path):
            self._create_backup(path)
        if code and not code.endswith("\n"):
            code += "\n"
        try:
            with open(path, "wb") as f:
                f.seek(0); f.truncate()
                f.write(code.encode("utf-8"))
            self._append_console(f"Saved: {os.path.basename(path)}", "info")
        except Exception as e:
            self._append_console(f"SAVE ERROR: {e}", "error")

    def _create_backup(self, file_path):
        if not ENABLE_BACKUPS: return
        try:
            backup_root = os.path.join(os.path.dirname(file_path), "_backups")
            ensure_directory(backup_root)
            script_name = os.path.splitext(os.path.basename(file_path))[0]
            script_backup_dir = os.path.join(backup_root, script_name)
            ensure_directory(script_backup_dir)
            if not os.path.abspath(script_backup_dir).startswith(
                    os.path.abspath(backup_root)):
                self._append_console("Backup aborted: unsafe path.", "error"); return
            backup_file = os.path.join(script_backup_dir, f"{timestamp_string()}.bak")
            shutil.copy2(file_path, backup_file)
            backups = sorted(
                f for f in os.listdir(script_backup_dir) if f.endswith(".bak")
            )
            for old in backups[:max(0, len(backups) - MAX_BACKUPS)]:
                os.remove(os.path.join(script_backup_dir, old))
            self._append_console(f"Backup: {os.path.basename(backup_file)}", "info")
        except Exception as e:
            self._append_console(f"Backup failed: {e}", "error")

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def _add_to_history(self, code):
        if not code.strip(): return
        self.history_items.insert(
            0, (code, getattr(self.tab_widget.currentWidget(), "file_path", None))
        )
        if len(self.history_items) > self.max_history:
            self.history_items = self.history_items[:self.max_history]
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.history_list.clear()
        for idx, (code, script_path) in enumerate(self.history_items, 1):
            first = code.strip().splitlines()[0] if code.strip().splitlines() else ""
            preview = first[:57] + ("..." if len(first) > 57 else "")
            item = QtWidgets.QListWidgetItem(f"{idx}: {preview}")
            item.setData(QtCore.Qt.UserRole, (code, script_path))
            self.history_list.addItem(item)
        self._update_status_bar()

    def _on_history_double_clicked(self, item):
        data = item.data(QtCore.Qt.UserRole)
        if not data: return
        code, script_path = data
        if script_path and os.path.exists(script_path):
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if getattr(tab, "file_path", None) == script_path:
                    self.tab_widget.setCurrentIndex(i)
                    tab.setPlainText(code)
                    return
        self._new_tab("History Snippet", code)

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def refresh_variables(self):
        self.vars_list.clear()
        for key, value in sorted(self.exec_namespace.items()):
            if key == "__builtins__": continue
            self.vars_list.addItem(f"{key} : {type(value).__name__}")

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _update_status_bar(self):
        repo = self.current_repo_path or BASE_SHARED_PATH
        file_count = 0
        if os.path.exists(repo):
            if USE_SINGLE_SHARED_FOLDER:
                try:
                    file_count = sum(
                        1 for f in os.listdir(repo) if f.lower().endswith(".py")
                    )
                except Exception:
                    pass
            else:
                for root, _, files in os.walk(repo):
                    file_count += sum(1 for f in files if f.lower().endswith(".py"))
        self.status_bar.setText(
            f"Repo: {repo} | Files: {file_count} | "
            f"Backups: {MAX_BACKUPS if ENABLE_BACKUPS else 0} | "
            f"History: {len(self.history_items)}/{self.max_history} | "
            f"User: {self.current_user}"
        )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

_BRIDGE_INSTANCE = None

def start_nuke_code_bridge():
    global _BRIDGE_INSTANCE
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    for widget in app.topLevelWidgets():
        if isinstance(widget, NukeCodeBridge):
            widget.raise_()
            widget.activateWindow()
            return widget
    _BRIDGE_INSTANCE = NukeCodeBridge()
    _BRIDGE_INSTANCE.resize(1200, 800)
    _BRIDGE_INSTANCE.show()
    return _BRIDGE_INSTANCE


if __name__ == "__main__":
    if nuke:
        start_nuke_code_bridge()
    else:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        win = start_nuke_code_bridge()
        sys.exit(app.exec_())

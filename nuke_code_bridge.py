# untested release, please download release zip for the latest working version NukeCodeBridge v0.12 (Final Optimized Production Build)
# Network-Based Script Manager & Python Editor for Foundry Nuke

from __future__ import print_function
import re, os, sys, traceback, datetime, shutil, json, __main__

try:
    import nuke
except ImportError:
    nuke = None

# --- Universal Compatibility Layer ---
try:
    from PySide6 import QtWidgets, QtGui, QtCore
    UniversalShortcut = QtGui.QShortcut 
except ImportError:
    from PySide2 import QtWidgets, QtGui, QtCore
    UniversalShortcut = QtWidgets.QShortcut

# --- Configuration ---
BASE_SHARED_PATH = r"X:\yourshared_envirement\python\nuke_code_bridge"
SHOW_RUN_CONFIRMATION = True
USE_SINGLE_SHARED_FOLDER = False
ENABLE_BACKUPS = True
MAX_BACKUPS = 3
MAX_HISTORY_ITEMS = 25

# --- Utilities ---
def ensure_directory(path):
    if not os.path.exists(path): os.makedirs(path)

def get_user_name():
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown_user"

# --- Components ---
class StreamRedirector(QtCore.QObject):
    message_emitted = QtCore.Signal(str)
    def __init__(self, console_widget):
        super(StreamRedirector, self).__init__()
        self.console_widget = console_widget
        self.message_emitted.connect(self.console_widget.appendPlainText)
    def write(self, text):
        if text: self.message_emitted.emit(text.rstrip("\n"))
    def flush(self): pass
    def __enter__(self):
        self._old_out, self._old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = self
        return self
    def __exit__(self, *args):
        sys.stdout, sys.stderr = self._old_out, self._old_err

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.code_editor = editor
    def sizeHint(self): return QtCore.QSize(self.code_editor.lineNumberAreaWidth(), 0)
    def paintEvent(self, event): self.code_editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
    zoomChanged = QtCore.Signal(int)
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.setFont(QtGui.QFont("Consolas", 10))
        self.setStyleSheet("QPlainTextEdit { background-color: #1E1E1E; color: #D4D4D4; selection-background-color: #264F78; border: none; }")
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._current_zoom = 0
        self.file_path = None
        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.highlightOccurrences)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits, max_val = 1, max(1, self.blockCount())
        while max_val >= 10: max_val //= 10; digits += 1
        return 40 + (self.fontMetrics().horizontalAdvance("9") * digits)

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy: self._line_number_area.scroll(0, dy)
        else: self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()): self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super(CodeEditor, self).resizeEvent(event)
        self._line_number_area.setGeometry(0, 0, self.lineNumberAreaWidth(), self.height())

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor(35, 35, 35))
        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QtGui.QColor(133, 133, 133))
                painter.drawText(0, top, self.lineNumberAreaWidth() - 15, self.fontMetrics().height(), QtCore.Qt.AlignRight, str(block_num + 1))
            block = block.next(); top = bottom; bottom = top + int(self.blockBoundingRect(block).height()); block_num += 1

    def highlightCurrentLine(self):
        extra = []
        if not self.isReadOnly():
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format.setBackground(QtGui.QColor(60, 60, 60, 80))
            sel.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor(); sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    def highlightOccurrences(self):
        cursor = self.textCursor(); cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        if not word or not word.isidentifier(): return
        fmt = QtGui.QTextCharFormat(); fmt.setBackground(QtGui.QColor(80, 80, 120, 120))
        selections = self.extraSelections()[:1]
        find_cursor = QtGui.QTextCursor(self.document())
        while not (find_cursor := self.document().find(word, find_cursor)).isNull():
            sel = QtWidgets.QTextEdit.ExtraSelection(); sel.cursor, sel.format = find_cursor, fmt
            selections.append(sel)
        self.setExtraSelections(selections)

    def wheelEvent(self, event):
        if event.modifiers() & QtCore.Qt.ControlModifier:
            self.zoomIn(1) if event.angleDelta().y() > 0 else self.zoomOut(1)
            event.accept()
        else: super(CodeEditor, self).wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection(): self._indent_selection(cursor, True)
            else: self.insertPlainText(" " * 4)
            return
        elif event.key() == QtCore.Qt.Key_Backtab:
            self._indent_selection(self.textCursor(), False)
            return
        super(CodeEditor, self).keyPressEvent(event)

    def _indent_selection(self, cursor, indent=True):
        start, end = self.document().findBlock(cursor.selectionStart()), self.document().findBlock(cursor.selectionEnd() - 1)
        cursor.beginEditBlock()
        block = start
        while block.isValid():
            tc = QtGui.QTextCursor(block); tc.movePosition(QtGui.QTextCursor.StartOfBlock)
            if indent: tc.insertText(" " * 4)
            else:
                text = block.text()
                remove = 0
                while remove < 4 and remove < len(text) and text[remove].isspace(): remove += 1
                for _ in range(remove): tc.deleteChar()
            if block == end: break
            block = block.next()
        cursor.endEditBlock()

class PythonHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super(PythonHighlighter, self).__init__(document)
        self.rules = []
        def fmt(c, b=False):
            f = QtGui.QTextCharFormat(); f.setForeground(QtGui.QColor(c))
            if b: f.setFontWeight(QtGui.QFont.Bold)
            return f
        
        keywords = ["def", "class", "import", "from", "return", "if", "elif", "else", "try", "except", "for", "while", "in", "and", "or", "not", "with", "as", "lambda"]
        for kw in keywords: self.rules.append((rf"\b{kw}\b", fmt("#C586C0")))
        self.rules.extend([
            (r'"[^"\\]*(\\.[^"\\]*)*"', fmt("#CE9178")), (r"'[^'\\]*(\\.[^'\\]*)*'", fmt("#CE9178")),
            (r"#.*", fmt("#6A9955")), (r"\bclass\s+(\w+)", fmt("#4EC9B0", True)),
            (r"\bdef\s+(\w+)", fmt("#DCDCAA")), (r"\b[0-9]+\b", fmt("#B5CEA8"))
        ])

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text): self.setFormat(match.start(), match.end() - match.start(), fmt)

# --- Main Window ---
class NukeCodeBridge(QtWidgets.QWidget):
    def __init__(self, parent=None):
        if parent is None and nuke: parent = QtWidgets.QApplication.activeWindow()
        super(NukeCodeBridge, self).__init__(parent)
        self.setWindowTitle("NukeCodeBridge v0.12")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.exec_namespace = {"nuke": nuke}
        self.current_user = get_user_name()
        self.history_items = []

        self._init_paths()
        self._init_ui()
        self._refresh_script_list()
        self._restore_session_state()

    def _init_paths(self):
        self.current_repo_path = os.path.join(BASE_SHARED_PATH, self.current_user)
        ensure_directory(self.current_repo_path)

    def _init_ui(self):
        lyt = QtWidgets.QVBoxLayout(self)
        
        # Header
        top_lyt = QtWidgets.QHBoxLayout()
        self.filename_edit = QtWidgets.QLineEdit(); self.filename_edit.setPlaceholderText("script_name.py")
        top_lyt.addWidget(QtWidgets.QLabel("Active Script Name:")); top_lyt.addWidget(self.filename_edit)
        lyt.addLayout(top_lyt)

        # Main Splitter
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        lyt.addWidget(self.main_splitter, 1)

        # Sidebar
        side_widget = QtWidgets.QWidget(); side_lyt = QtWidgets.QVBoxLayout(side_widget)
        self.user_combo = QtWidgets.QComboBox(); self.user_combo.currentTextChanged.connect(self._on_user_changed)
        self._populate_users()
        self.search_edit = QtWidgets.QLineEdit(); self.search_edit.setPlaceholderText("Search scripts..."); self.search_edit.textChanged.connect(self._refresh_script_list)
        self.script_list = QtWidgets.QListWidget(); self.script_list.itemDoubleClicked.connect(self._on_script_double_clicked)
        self.history_list = QtWidgets.QListWidget(); self.history_list.itemDoubleClicked.connect(self._on_history_double_clicked)
        
        side_lyt.addWidget(QtWidgets.QLabel("User:")); side_lyt.addWidget(self.user_combo)
        side_lyt.addWidget(self.search_edit); side_lyt.addWidget(self.script_list, 3)
        side_lyt.addWidget(QtWidgets.QLabel("Execution History:")); side_lyt.addWidget(self.history_list, 1)
        self.main_splitter.addWidget(side_widget)

        # Editor Area
        right_widget = QtWidgets.QWidget(); right_lyt = QtWidgets.QVBoxLayout(right_widget)
        
        # Search/Replace Bar
        self.search_bar = QtWidgets.QWidget(); self.search_bar.hide(); sb_lyt = QtWidgets.QHBoxLayout(self.search_bar)
        self.editor_search_edit = QtWidgets.QLineEdit(); self.editor_search_edit.textChanged.connect(self._do_editor_search)
        self.editor_replace_edit = QtWidgets.QLineEdit()
        replace_btn = QtWidgets.QPushButton("Replace All"); replace_btn.clicked.connect(self._replace_all)
        sb_lyt.addWidget(QtWidgets.QLabel("Find:")); sb_lyt.addWidget(self.editor_search_edit)
        sb_lyt.addWidget(QtWidgets.QLabel("Replace:")); sb_lyt.addWidget(self.editor_replace_edit); sb_lyt.addWidget(replace_btn)
        right_lyt.addWidget(self.search_bar)

        self.v_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.tab_widget = QtWidgets.QTabWidget(); self.tab_widget.setTabsClosable(True); self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.v_splitter.addWidget(self.tab_widget)
        
        # Console
        console_widget = QtWidgets.QWidget(); con_lyt = QtWidgets.QVBoxLayout(console_widget)
        header_lyt = QtWidgets.QHBoxLayout(); self.status_light = QtWidgets.QLabel("●")
        self.status_light.setStyleSheet("color: #555; font-size: 18px;")
        self.console_mode = QtWidgets.QComboBox(); self.console_mode.addItems(["All", "Errors Only", "Actions/Info"]); self.console_mode.currentIndexChanged.connect(self._apply_console_filter)
        header_lyt.addWidget(self.status_light); header_lyt.addWidget(QtWidgets.QLabel("Console:")); header_lyt.addStretch(); header_lyt.addWidget(self.console_mode)
        self.console_output = QtWidgets.QPlainTextEdit(); self.console_output.setReadOnly(True); self.console_output.setStyleSheet("background-color: #1A1A1A; color: #D4D4D4;")
        con_lyt.addLayout(header_lyt); con_lyt.addWidget(self.console_output)
        self.v_splitter.addWidget(console_widget)
        right_lyt.addWidget(self.v_splitter)

        # Bottom Buttons
        btn_lyt = QtWidgets.QHBoxLayout()
        for label, func in [("Save", self.save_script), ("Save As", self.save_script_as), ("Run Code", self.execute_code), ("Run Sel", self.execute_selection), ("Refresh Vars", self.refresh_variables)]:
            btn = QtWidgets.QPushButton(label); btn.clicked.connect(func); btn_lyt.addWidget(btn)
        right_lyt.addLayout(btn_lyt)
        self.main_splitter.addWidget(right_widget)

        # Status Bar
        self.status_bar = QtWidgets.QLabel(); self.status_bar.setStyleSheet("font-size: 10px; color: #888;")
        lyt.addWidget(self.status_bar)

        # Shortcuts
        UniversalShortcut(QtGui.QKeySequence("Ctrl+S"), self).activated.connect(self.save_script)
        UniversalShortcut(QtGui.QKeySequence("Ctrl+Return"), self).activated.connect(self.execute_code)
        UniversalShortcut(QtGui.QKeySequence("Ctrl+Shift+Return"), self).activated.connect(self.execute_selection)
        UniversalShortcut(QtGui.QKeySequence("Ctrl+F"), self).activated.connect(lambda: (self.search_bar.show(), self.editor_search_edit.setFocus()))
        UniversalShortcut(QtGui.QKeySequence("Esc"), self).activated.connect(self.search_bar.hide)

        self._new_tab("Untitled")

    def _append_console(self, text, msg_type="info"):
        self.console_output.moveCursor(QtGui.QTextCursor.End)
        colors = {"info": "#D4D4D4", "error": "#F44747", "action": "#9CDCFE"}
        fmt = QtGui.QTextCharFormat(); fmt.setForeground(QtGui.QColor(colors.get(msg_type, "#D4D4D4")))
        self.console_output.setCurrentCharFormat(fmt)
        self.console_output.insertPlainText(text + "\n")
        state = 1 if msg_type == "error" else 2 if msg_type == "action" else 0
        self.console_output.document().lastBlock().setUserState(state)
        self.console_output.ensureCursorVisible()
        self._apply_console_filter()

    def _apply_console_filter(self):
        mode = self.console_mode.currentText()
        block = self.console_output.document().begin()
        while block.isValid():
            state = block.userState()
            visible = (mode == "All") or (mode == "Errors Only" and state == 1) or (mode == "Actions/Info" and state in (0, 2))
            block.setVisible(visible); block = block.next()
        self.console_output.viewport().update()

    def execute_code(self, code=None):
        if code is None:
            editor = self.tab_widget.currentWidget()
            code = editor.toPlainText() if editor else ""
        if not code.strip(): return
        
        self.console_output.clear(); self.status_light.setStyleSheet("color: #CCA700; font-size: 18px;")
        success = True
        with StreamRedirector(self.console_output):
            try: exec(code, self.exec_namespace)
            except Exception:
                success = False
                self._append_console("-" * 50, "error")
                self._append_console(traceback.format_exc(), "error")
                self._append_console("-" * 50, "error")
        
        self.status_light.setStyleSheet("color: #6A9955; font-size: 18px;" if success else "color: #F44747; font-size: 18px;")
        self._add_to_history(code)

    def execute_selection(self):
        editor = self.tab_widget.currentWidget()
        if editor:
            sel = editor.textCursor().selectedText().replace('\u2029', '\n')
            self.execute_code(sel if sel.strip() else editor.toPlainText())

    def save_script(self):
        editor = self.tab_widget.currentWidget()
        if not editor: return
        path = editor.file_path or os.path.join(self.current_repo_path, self.filename_edit.text() or "untitled.py")
        if not path.endswith(".py"): path += ".py"
        
        if ENABLE_BACKUPS and os.path.exists(path): self._create_backup(path)
        try:
            with open(path, "w") as f: f.write(editor.toPlainText())
            editor.file_path = path
            self.tab_widget.setTabText(self.tab_widget.indexOf(editor), os.path.basename(path))
            self._append_console(f"Saved: {path}", "action")
            self._refresh_script_list()
        except Exception as e: self._append_console(str(e), "error")

    def save_script_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Script As", self.current_repo_path, "Python Files (*.py)")
        if path:
            self.tab_widget.currentWidget().file_path = path
            self.save_script()

    def _create_backup(self, path):
        bdir = os.path.join(os.path.dirname(path), "_backups", os.path.splitext(os.path.basename(path))[0])
        ensure_directory(bdir)
        shutil.copy2(path, os.path.join(bdir, datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"))
        backups = sorted([os.path.join(bdir, f) for f in os.listdir(bdir)])
        if len(backups) > MAX_BACKUPS: os.remove(backups[0])

    def _new_tab(self, title, content="", file_path=None):
        editor = CodeEditor(); editor.setPlainText(content); editor.file_path = file_path
        PythonHighlighter(editor.document())
        editor.textChanged.connect(self._save_session_state)
        idx = self.tab_widget.addTab(editor, title); self.tab_widget.setCurrentIndex(idx)
        return editor

    def _close_tab(self, index):
        if self.tab_widget.count() > 1: self.tab_widget.removeTab(index)

    def _add_to_history(self, code):
        self.history_items.insert(0, code)
        self.history_list.clear()
        for c in self.history_items[:MAX_HISTORY_ITEMS]:
            self.history_list.addItem(c.splitlines()[0][:40] + "...")

    def _on_script_double_clicked(self, item):
        path = item.data(QtCore.Qt.UserRole)
        with open(path, "r") as f: self._new_tab(os.path.basename(path), f.read(), path)

    def _on_history_double_clicked(self, item):
        self._new_tab("History Snippet", self.history_items[self.history_list.row(item)])

    def _refresh_script_list(self):
        self.script_list.clear(); search = self.search_edit.text().lower()
        if os.path.exists(self.current_repo_path):
            for f in os.listdir(self.current_repo_path):
                if f.endswith(".py") and search in f.lower():
                    it = QtWidgets.QListWidgetItem(f); it.setData(QtCore.Qt.UserRole, os.path.join(self.current_repo_path, f))
                    self.script_list.addItem(it)
        self.status_bar.setText(f"Repo: {self.current_repo_path} | User: {self.current_user}")

    def _populate_users(self):
        users = [self.current_user, "all_users"]
        if os.path.exists(BASE_SHARED_PATH):
            users.extend([d for d in os.listdir(BASE_SHARED_PATH) if os.path.isdir(os.path.join(BASE_SHARED_PATH, d)) and d not in users])
        self.user_combo.addItems(users)

    def _on_user_changed(self, user):
        self.current_repo_path = os.path.join(BASE_SHARED_PATH, "" if user == "all_users" else user)
        ensure_directory(self.current_repo_path); self._refresh_script_list()

    def _replace_all(self):
        editor = self.tab_widget.currentWidget()
        if editor:
            txt = editor.toPlainText().replace(self.editor_search_edit.text(), self.editor_replace_edit.text())
            editor.setPlainText(txt)

    def _do_editor_search(self):
        editor = self.tab_widget.currentWidget()
        if editor: editor.find(self.editor_search_edit.text())

    def _save_session_state(self):
        data = [{"title": self.tab_widget.tabText(i), "content": self.tab_widget.widget(i).toPlainText(), "path": getattr(self.tab_widget.widget(i), "file_path", None)} for i in range(self.tab_widget.count())]
        with open(os.path.join(self.current_repo_path, ".session.json"), "w") as f: json.dump(data, f)

    def _restore_session_state(self):
        path = os.path.join(self.current_repo_path, ".session.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    for item in json.load(f): self._new_tab(item["title"], item["content"], item.get("path"))
                if self.tab_widget.count() > 1: self.tab_widget.removeTab(0)
            except: pass

    def refresh_variables(self):
        self._append_console("--- Session Variables ---", "action")
        for k, v in self.exec_namespace.items():
            if not k.startswith("__"): self._append_console(f"{k}: {type(v).__name__}")

if __name__ == "__main__":
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = NukeCodeBridge(); win.resize(1200, 800); win.show()
    if not nuke: sys.exit(app.exec_())


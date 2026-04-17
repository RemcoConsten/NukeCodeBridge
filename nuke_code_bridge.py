import nuke
import os
import getpass
import re
import subprocess

# --- PySide Compatibility ---
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

# ============================
# === GLOBAL CONFIG ===
# ============================
VERSION = "v0.7 beta"
AUTHOR = "Remco Consten"
YEAR = "2026"

# <<< EDIT THIS BASE PATH FOR YOUR STUDIO for example:r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"  >>>
BASE_SHARED_PATH = r"REPLACE_WITH_YOUR_PATH" 

SHOW_RUN_CONFIRMATION = True
USE_SINGLE_SHARED_FOLDER = False

if USE_SINGLE_SHARED_FOLDER:
    SHARED_SERVER_PATH = os.path.join(BASE_SHARED_PATH, "Shared")
    CURRENT_USER = "Shared"
else:
    SHARED_SERVER_PATH = BASE_SHARED_PATH
    try:
        CURRENT_USER = getpass.getuser()
    except Exception:
        CURRENT_USER = os.environ.get("USERNAME", "default_user")

# ============================
# === CUSTOM WIDGETS ===
# ============================

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        
        font = QtGui.QFont("Courier New", 11) # Slightly larger font
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Ensure the editor expands to fill space
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def lineNumberAreaWidth(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1
        return 25 + self.fontMetrics().horizontalAdvance('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super(CodeEditor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            line_color = QtGui.QColor(QtCore.Qt.yellow).lighter(160)
            line_color.setAlpha(25)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor("#2b2b2b"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QtGui.QColor("#888888"))
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

class PythonHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super(PythonHighlighter, self).__init__(document)
        self.rules = []
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtGui.QColor("#E28E46"))
        keywords = r'\b(def|class|import|from|return|if|elif|else|try|except|for|while|in|and|or|not|pass|print|True|False|None)\b'
        self.rules.append((keywords, keyword_format))
        
        string_format = QtGui.QTextCharFormat()
        string_format.setForeground(QtGui.QColor("#6A8759"))
        self.rules.append((r'".*?"|\'.*?\'', string_format))
        
        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtGui.QColor("#808080"))
        self.rules.append((r'#.*', comment_format))

    def highlightBlock(self, text):
        for pattern, format_ in self.rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format_)

# ============================
# === MAIN UI CLASS ===
# ============================

class NukeCodeBridgeUI(QtWidgets.QWidget):
    def __init__(self):
        super(NukeCodeBridgeUI, self).__init__()
        self.current_user = CURRENT_USER
        
        if not os.path.exists(SHARED_SERVER_PATH):
            try: os.makedirs(SHARED_SERVER_PATH)
            except: pass

        self.initUI()
        self.refresh_users()

    def initUI(self):
        self.setWindowTitle(f"NukeCodeBridge {VERSION}")
        self.resize(1100, 750) # Increased default window size
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        # Main Layout (Vertical)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 5)
        
        # Splitter for dynamic resizing
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # --- Left Panel ---
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        self.user_dropdown = QtWidgets.QComboBox()
        self.user_dropdown.currentIndexChanged.connect(self.refresh_scripts)
        
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.itemClicked.connect(self.load_script)
        self.list_widget.customContextMenuRequested.connect(self.show_list_context_menu)
        
        self.new_btn = QtWidgets.QPushButton("New Script")
        self.new_btn.setFixedHeight(30)
        self.new_btn.clicked.connect(self.clear_editor)
        
        left_layout.addWidget(QtWidgets.QLabel("User:"))
        left_layout.addWidget(self.user_dropdown)
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.list_widget)
        left_layout.addWidget(self.new_btn)

        # --- Right Panel ---
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Script Name...")
        self.name_input.setFixedHeight(25)
        
        self.code_editor = CodeEditor()
        self.highlighter = PythonHighlighter(self.code_editor.document())
        
        btn_layout = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setFixedHeight(35)
        self.save_btn.clicked.connect(self.save_script)
        
        self.run_btn = QtWidgets.QPushButton("Run Code")
        self.run_btn.setFixedHeight(35)
        self.run_btn.setStyleSheet("background-color: #3d6e3d; font-weight: bold; color: #fff;")
        self.run_btn.clicked.connect(self.run_script)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.run_btn)
        
        right_layout.addWidget(self.name_input)
        right_layout.addWidget(self.code_editor)
        right_layout.addLayout(btn_layout)

        # Splitter Assembly
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        
        # Initial proportions: Sidebar 200px, Editor gets the rest
        self.splitter.setSizes([200, 900])
        self.splitter.setStretchFactor(1, 1) # Editor expands, sidebar stays relatively stable

        # --- Status Bar & Footer ---
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setStyleSheet("color: #888; border-top: 1px solid #333; font-size: 10px;")

        footer_layout = QtWidgets.QHBoxLayout()
        footer_text = f"NukeCodeBridge {VERSION} | © {YEAR} {AUTHOR}"
        self.credit_label = QtWidgets.QLabel(footer_text)
        self.credit_label.setStyleSheet("color: #444; font-size: 9px;")
        self.credit_label.setAlignment(QtCore.Qt.AlignRight)

        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.status_bar)
        main_layout.addWidget(self.credit_label)

    # --- Methods ---

    def refresh_users(self):
        self.user_dropdown.blockSignals(True)
        self.user_dropdown.clear()
        if os.path.exists(SHARED_SERVER_PATH):
            users = [d for d in os.listdir(SHARED_SERVER_PATH) if os.path.isdir(os.path.join(SHARED_SERVER_PATH, d))]
            if not USE_SINGLE_SHARED_FOLDER:
                if self.current_user not in users: users.append(self.current_user)
            self.user_dropdown.addItems(sorted(users))
            self.user_dropdown.setCurrentText(self.current_user)
        self.user_dropdown.blockSignals(False)
        self.refresh_scripts()

    def refresh_scripts(self):
        self.list_widget.clear()
        selected_user = self.user_dropdown.currentText()
        user_path = os.path.join(SHARED_SERVER_PATH, selected_user)
        
        count = 0
        if os.path.exists(user_path):
            files = [f for f in sorted(os.listdir(user_path)) if f.endswith(('.py', '.txt'))]
            for f in files:
                self.list_widget.addItem(f)
            count = len(files)
        
        self.status_bar.showMessage(f" Repository: {selected_user} | Count: {count}")

    def show_list_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return
        menu = QtWidgets.QMenu()
        act_open = menu.addAction("Open File Location")
        act_del = menu.addAction("Delete Script")
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        user_dir = os.path.join(SHARED_SERVER_PATH, self.user_dropdown.currentText())
        if action == act_open:
            if os.name == 'nt': os.startfile(user_dir)
            else: subprocess.call(['open', user_dir])
        elif action == act_del:
            if nuke.ask(f"Permanently delete '{item.text()}'?"):
                os.remove(os.path.join(user_dir, item.text()))
                self.refresh_scripts()

    def clear_editor(self):
        self.name_input.clear()
        self.code_editor.setPlainText("")
        self.status_bar.showMessage("New script initialized.", 3000)

    def load_script(self, item):
        path = os.path.join(SHARED_SERVER_PATH, self.user_dropdown.currentText(), item.text())
        try:
            with open(path, 'r') as f: self.code_editor.setPlainText(f.read())
            self.name_input.setText(item.text().replace('.py', ''))
        except Exception as e: nuke.message(f"Error loading script:\n{e}")

    def save_script(self):
        name = self.name_input.text().strip()
        if not name: return
        if not name.endswith('.py'): name += '.py'
        save_user = "Shared" if USE_SINGLE_SHARED_FOLDER else self.current_user
        user_dir = os.path.join(SHARED_SERVER_PATH, save_user)
        if not os.path.exists(user_dir): os.makedirs(user_dir)
        path = os.path.join(user_dir, name)
        try:
            with open(path, 'w') as f: f.write(self.code_editor.toPlainText())
            self.refresh_users()
            self.user_dropdown.setCurrentText(save_user)
            self.status_bar.showMessage(f"Saved to {save_user}", 4000)
        except Exception as e: nuke.message(f"Error saving:\n{e}")

    def run_script(self):
        code = self.code_editor.toPlainText()
        if not code.strip(): return
        if SHOW_RUN_CONFIRMATION and not nuke.ask("Execute code?"): return
        try: exec(code, globals())
        except Exception as e: nuke.message(f"Script Error:\n{e}")

# ============================
# === LAUNCHER ===
# ============================

_bridge_instance = None

def start_nuke_code_bridge():
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NukeCodeBridgeUI()
    _bridge_instance.show()

if __name__ == '__main__':
    start_nuke_code_bridge()

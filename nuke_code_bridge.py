import nuke
import os
import getpass
import re

# ============================
# === STUDIO CONFIGURATION ===
# ============================

# <<< EDIT THIS BASE PATH FOR YOUR STUDIO >>>
# Windows example: r"\\server\share\SharedNukeScripts"
# Linux   example: "/mnt/studio/SharedNukeScripts"
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"   # ← Change this!

# === PER-USER FOLDERS (DEFAULT) ===
# Each user gets their own subfolder
SHARED_SERVER_PATH = BASE_SHARED_PATH

# === SINGLE SHARED FOLDER MODE (optional) ===
# Uncomment these lines to switch to one common folder:
# SHARED_SERVER_PATH = os.path.join(BASE_SHARED_PATH, "Shared")
# CURRENT_USER = "Shared"

# Safe current user detection
try:
    CURRENT_USER = getpass.getuser()
except Exception:
    CURRENT_USER = (os.environ.get("USER") or 
                    os.environ.get("USERNAME") or 
                    os.environ.get("LOGNAME") or 
                    "default_user")


# --- PySide Compatibility (Nuke 13 vs 14/15+) ---
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui


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
        self.current_font_size = 10
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

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
            line_color.setAlpha(30)
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

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.insertPlainText("    ")
            return
            
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            cursor = self.textCursor()
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()
            leading_spaces = len(current_line) - len(current_line.lstrip(' '))
            if current_line.strip().endswith(':'):
                leading_spaces += 4
                
            super(CodeEditor, self).keyPressEvent(event)
            
            if leading_spaces > 0:
                self.insertPlainText(" " * leading_spaces)
            return

        super(CodeEditor, self).keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.current_font_size += 1
            else:
                self.current_font_size = max(6, self.current_font_size - 1)
            font = self.font()
            font.setPointSize(self.current_font_size)
            self.setFont(font)
            return
        super(CodeEditor, self).wheelEvent(event)


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super(PythonHighlighter, self).__init__(document)
        self.rules = []
        
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtGui.QColor("#E28E46"))
        keyword_format.setFontWeight(QtGui.QFont.Bold)
        keywords = r'\b(def|class|import|from|return|if|elif|else|try|except|for|while|in|and|or|not|pass|global|print|True|False|None)\b'
        self.rules.append((keywords, keyword_format))

        string_format = QtGui.QTextCharFormat()
        string_format.setForeground(QtGui.QColor("#6A8759"))
        self.rules.append((r'".*?"|\'.*?\'', string_format))
        
        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtGui.QColor("#808080"))
        comment_format.setFontItalic(True)
        self.rules.append((r'#.*', comment_format))

    def highlightBlock(self, text):
        for pattern, format_ in self.rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format_)


# ============================
# === MAIN UI CLASS ===
# ============================

class NukeCodeBridge(QtWidgets.QWidget):
    def __init__(self):
        super(NukeCodeBridge, self).__init__()
        
        self.current_user = CURRENT_USER
        
        if not os.path.exists(SHARED_SERVER_PATH):
            try:
                os.makedirs(SHARED_SERVER_PATH)
            except Exception as e:
                print(f"Could not create or access shared path: {e}")
        
        self.is_modified = False
        self.currently_loaded_path = ""

        self.initUI()
        self.refresh_users()

    def initUI(self):
        self.setWindowTitle("NukeCodeBridge v0.5 beta — Remco Consten")
        self.resize(800, 550)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        main_layout = QtWidgets.QHBoxLayout()

        # Left panel
        left_layout = QtWidgets.QVBoxLayout()
        
        self.user_dropdown = QtWidgets.QComboBox()
        self.user_dropdown.currentIndexChanged.connect(self.refresh_scripts)
        
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search scripts...")
        self.search_bar.textChanged.connect(self.filter_scripts)
        
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemClicked.connect(self.load_script)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        self.refresh_btn = QtWidgets.QPushButton("Refresh All")
        self.refresh_btn.clicked.connect(self.refresh_users)

        left_layout.addWidget(QtWidgets.QLabel("Select User:"))
        left_layout.addWidget(self.user_dropdown)
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.list_widget)
        left_layout.addWidget(self.refresh_btn)

        # Right panel
        right_layout = QtWidgets.QVBoxLayout()
        
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter script name (e.g., auto_render)")
        
        self.code_editor = CodeEditor() 
        self.code_editor.setPlaceholderText("Paste or write your Python code here...")
        self.code_editor.textChanged.connect(self.mark_as_modified)
        
        font = QtGui.QFont("Courier")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(10)
        self.code_editor.setFont(font)
        self.highlighter = PythonHighlighter(self.code_editor.document()) 
        
        btn_layout = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Save to Current User")
        self.save_btn.clicked.connect(self.save_script)
        
        self.run_btn = QtWidgets.QPushButton("Run Code")
        self.run_btn.setStyleSheet("background-color: #2b5c2b; font-weight: bold;")
        self.run_btn.clicked.connect(self.run_script)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.run_btn)

        right_layout.addWidget(self.name_input)
        right_layout.addWidget(self.code_editor)
        right_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

    # --- POPUPS & SAFETY CHECKS ---
    def show_popup(self, title, message, is_error=False):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if is_error:
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        else:
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.exec_()

    def check_unsaved_changes(self):
        if self.is_modified:
            reply = QtWidgets.QMessageBox.question(
                self, 'Unsaved Changes', 
                "You have unsaved changes in the editor!\nDo you want to discard them?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return False
        return True

    def mark_as_modified(self):
        if self.code_editor.toPlainText() or self.currently_loaded_path:
            self.is_modified = True
            self.setWindowTitle("NukeCodeBridge v0.5 beta — Remco Consten *")

    def closeEvent(self, event):
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()

    # --- FILTERING & CONTEXT MENU ---
    def filter_scripts(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if item is not None:
            menu = QtWidgets.QMenu()
            run_action = menu.addAction("Run Script")
            menu.addSeparator()
            rename_action = menu.addAction("Rename Script")
            copy_action = menu.addAction("Copy Server Path")
            menu.addSeparator() 
            delete_action = menu.addAction("Delete Script")
            
            global_position = self.list_widget.viewport().mapToGlobal(position)
            action = menu.exec_(global_position)
            
            if action == delete_action:
                self.delete_script(item)
            elif action == copy_action:
                self.copy_path(item)
            elif action == rename_action:
                self.rename_script(item)
            elif action == run_action:
                self.run_from_server(item)

    # --- RENAME, COPY, DELETE, RUN FROM SERVER ---
    def rename_script(self, item):
        selected_user = self.user_dropdown.currentText()
        old_filename = item.text()
        old_filepath = os.path.join(SHARED_SERVER_PATH, selected_user, old_filename)
        
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename Script", 
                                                      "Enter new name:", text=old_filename.rsplit('.', 1)[0])
        
        if ok and new_name.strip():
            if not new_name.endswith(('.py', '.txt')):
                new_name += '.py'
            new_filepath = os.path.join(SHARED_SERVER_PATH, selected_user, new_name)
            
            if os.path.exists(new_filepath):
                self.show_popup("Rename Error", f"A script named '{new_name}' already exists.", is_error=True)
                return
                
            try:
                os.rename(old_filepath, new_filepath)
                self.refresh_scripts()
                if self.currently_loaded_path == old_filepath:
                    self.name_input.setText(new_name.rsplit('.', 1)[0])
                    self.currently_loaded_path = new_filepath
            except Exception as e:
                self.show_popup("Rename Error", f"Failed to rename:\n{str(e)}", is_error=True)

    def copy_path(self, item):
        selected_user = self.user_dropdown.currentText()
        filepath = os.path.join(SHARED_SERVER_PATH, selected_user, item.text())
        QtWidgets.QApplication.clipboard().setText(filepath)
        self.show_popup("Copied", f"Path copied to clipboard:\n\n{filepath}")

    def delete_script(self, item):
        selected_user = self.user_dropdown.currentText()
        filepath = os.path.join(SHARED_SERVER_PATH, selected_user, item.text())
        
        reply = QtWidgets.QMessageBox.question(
            self, 'Confirm Delete', 
            f"Are you sure you want to delete '{item.text()}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.refresh_scripts()
                    if self.currently_loaded_path == filepath:
                        self.name_input.clear()
                        self.code_editor.clear()
                        self.is_modified = False
                        self.currently_loaded_path = ""
                    self.show_popup("Deleted", f"Successfully deleted '{item.text()}'.")
            except Exception as e:
                self.show_popup("Delete Error", f"Error deleting script:\n{str(e)}", is_error=True)

    def run_from_server(self, item):
        selected_user = self.user_dropdown.currentText()
        filepath = os.path.join(SHARED_SERVER_PATH, selected_user, item.text())
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                code = f.read()
            try:
                exec(code, globals())  # nosec
            except Exception as e:
                self.show_popup("Script Error", f"Error running script:\n{str(e)}", is_error=True)

    # --- REFRESH, LOAD, SAVE, RUN ---
    def refresh_users(self):
        self.user_dropdown.blockSignals(True)
        self.user_dropdown.clear()
        
        if os.path.exists(SHARED_SERVER_PATH):
            users = [d for d in os.listdir(SHARED_SERVER_PATH) 
                     if os.path.isdir(os.path.join(SHARED_SERVER_PATH, d))]
            
            if self.current_user not in users:
                users.append(self.current_user)
            
            users.sort()
            self.user_dropdown.addItems(users)
            
            if self.current_user in users:
                index = self.user_dropdown.findText(self.current_user)
                self.user_dropdown.setCurrentIndex(index)
                
        self.user_dropdown.blockSignals(False)
        self.refresh_scripts()

    def refresh_scripts(self):
        self.list_widget.clear()
        selected_user = self.user_dropdown.currentText()
        user_dir = os.path.join(SHARED_SERVER_PATH, selected_user)
        
        if not os.path.exists(user_dir):
            try:
                os.makedirs(user_dir)
            except Exception:  # nosec
                pass
                
        if os.path.exists(user_dir):
            for f in sorted(os.listdir(user_dir)):
                if f.endswith(('.py', '.txt')):
                    self.list_widget.addItem(f)
                    
        self.filter_scripts(self.search_bar.text())

    def load_script(self, item):
        if not self.check_unsaved_changes():
            return
            
        selected_user = self.user_dropdown.currentText()
        filename = item.text()
        self.name_input.setText(filename.rsplit('.', 1)[0])
        filepath = os.path.join(SHARED_SERVER_PATH, selected_user, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.code_editor.blockSignals(True)
                self.code_editor.setPlainText(f.read())
                self.code_editor.blockSignals(False)
                
            self.currently_loaded_path = filepath
            self.is_modified = False
            self.setWindowTitle("NukeCodeBridge v0.5 beta — Remco Consten")

    def save_script(self):
        selected_user = self.user_dropdown.currentText()
        name = self.name_input.text().strip()
        
        if not name:
            self.show_popup("Missing Name", "Please enter a name for your script.", is_error=True)
            return
            
        if not name.endswith(('.py', '.txt')):
            name += '.py'
            
        user_dir = os.path.join(SHARED_SERVER_PATH, selected_user)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            
        filepath = os.path.join(user_dir, name)
        
        if os.path.exists(filepath) and filepath != self.currently_loaded_path:
            reply = QtWidgets.QMessageBox.question(
                self, 'Confirm Overwrite', 
                f"A script named '{name}' already exists.\nDo you want to overwrite it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return
        
        code = self.code_editor.toPlainText()
        
        try:
            with open(filepath, 'w') as f:
                f.write(code)
            self.refresh_scripts()
            
            self.is_modified = False
            self.currently_loaded_path = filepath
            self.setWindowTitle("NukeCodeBridge v0.5 beta — Remco Consten")
            
            self.show_popup("Success", f"Saved: {name}\nUnder user: '{selected_user}'")
        except Exception as e:
            self.show_popup("Save Error", f"Error saving script:\n{str(e)}", is_error=True)

    def run_script(self):
        cursor = self.code_editor.textCursor()
        if cursor.hasSelection():
            code = cursor.selectedText().replace('\u2029', '\n')
        else:
            code = self.code_editor.toPlainText()
            
        if not code.strip():
            self.show_popup("Empty Script", "No code to run.", is_error=True)
            return
            
        try:
            exec(code, globals())  # nosec
        except Exception as e:
            self.show_popup("Script Error", f"Error running script:\n{str(e)}", is_error=True)


# ============================
# === LAUNCHER ===
# ============================

nuke_code_bridge_ui = None

def start_nuke_code_bridge():
    global nuke_code_bridge_ui
    nuke_code_bridge_ui = NukeCodeBridge()
    nuke_code_bridge_ui.show()

if __name__ == '__main__':
    start_nuke_code_bridge()

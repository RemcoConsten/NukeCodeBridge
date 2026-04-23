# NukeCodeBridge

![Version](https://img.shields.io/badge/version-v0.12-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![OS-Windows](https://img.shields.io/badge/Windows-Tested-green)
![OS-macOS](https://img.shields.io/badge/macOS-Experimental-yellow)
![OS-Linux](https://img.shields.io/badge/Linux-Experimental-yellow)
![Nuke](https://img.shields.io/badge/Nuke-13.0+-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Stars](https://img.shields.io/github/stars/RemcoConsten/NukeCodeBridge?style=social)

**Network-Based Script Manager & Python Editor for Foundry Nuke**

NukeCodeBridge is a lightweight, production‑oriented tool for VFX studios, teams, and solo artists.  
It allows you to **store, edit, run, and share Python scripts directly inside Nuke** using a shared network repository — no more Slack‑shared `.py` files or digging through old scripts.

---

## 🚀 What’s New Since v0.9

### **v0.12**
- Full **VS Code Dark+ themed editor**
- **Multi‑tab editing** (open multiple scripts at once)
- **Line numbers** with custom gutter
- **Current line highlight**
- **Word‑occurrence highlighting**
- **Zoom system**  
  - Ctrl + Mouse Wheel  
  - Ctrl + `+` / `-`  
  - Ctrl + `0` reset
- **Indent/unindent** (Tab / Shift+Tab)
- Multi‑line indentation support
- Improved **syntax highlighting**
- **Status light** (idle / running / success / error)
- Dark‑themed **console output panel**
- Safer, clearer **save** and **backup** behavior
- Cleaner, more modern UI layout

### **v0.11**
- Modular refactor (core, editor, UI, execution)
- Initial multi‑tab structure
- Improved network repository handling
- Basic save + backup system
- Console redirection via StreamRedirector
- Persistent execution namespace

### **v0.9**
- First public beta
- Single‑tab editor
- Basic network script loading
- Basic execution inside Nuke

---

## ✨ Features (v0.12)

### 📁 Network-Based Repository
- Central shared folder for all scripts
- Optional **per‑user subfolders** or **single shared folder**
- Auto‑creates missing directories
- Script list updates dynamically

### 📝 Multi‑Tab Python Editor
- Unlimited tabs
- “Untitled” tab on startup
- Each tab tracks its own file path
- Tabs are closable

### 🎨 VS Code‑Style Editing
- Dark+ theme
- Line numbers
- Current line highlight
- Word‑occurrence highlight
- Syntax highlighting (keywords, strings, comments)
- No line wrapping
- Undo/redo

### 🔧 Smart Editing Tools
- 4‑space indentation
- Multi‑line indent/unindent
- Shift+Tab unindent
- Zoom controls:
  - Ctrl + Mouse Wheel
  - Ctrl + `+` / `-`
  - Ctrl + `0` reset

### ▶️ Execution Engine
- Executes code in a **persistent namespace**
- Automatically injects `nuke` module (if available)
- Captures:
  - print() output
  - Errors
  - Tracebacks
- Status light:
  - Grey = idle  
  - Yellow = running  
  - Green = success  
  - Red = error  

### 🖥 Console Output Panel
- Read‑only
- Dark theme
- Auto‑scroll
- Shows:
  - Execution logs
  - Tracebacks
  - Save messages

### 💾 Saving & Backup System
- Save / Save As
- Ensures newline at end of file
- UTF‑8 encoding
- Optional backups (ENABLE_BACKUPS)
- Timestamped `.bak` files in `_backups` folder

### 📚 Script List Sidebar
- Lists all `.py` files in the repository
- Double‑click to open
- Supports per‑user or shared mode

---

## ⚙️ Configuration

At the top of `nuke_code_bridge.py`:

```
BASE_SHARED_PATH = r"Y:\\dev_remco\\SharedNukeScripts"
SHOW_RUN_CONFIRMATION = True
USE_SINGLE_SHARED_FOLDER = False

ENABLE_BACKUPS = True
MAX_BACKUPS = 3
MAX_HISTORY_ITEMS = 25
```

---

## 📦 Installation

1. Place `nuke_code_bridge.py` into your `.nuke` folder or shared pipeline module.

2. Add this to your `menu.py`:

```
import nuke
import nuke_code_bridge

nuke.menu("Nuke").addCommand(
    "Scripts/NukeCodeBridge",
    "nuke_code_bridge.start_nuke_code_bridge()"
)
```

3. Configure your repository path:

```
BASE_SHARED_PATH = r"X:/pipeline/nuke/scripts"
```

---

## 🧭 Usage

1. Open Nuke  
2. Go to **Scripts → NukeCodeBridge**  
3. Select a script from the sidebar or use the “Untitled” tab  
4. Edit your Python code  
5. Save / Save As  
6. Run the code  
7. View output in the console panel  

---

## 🗺 Roadmap (Updated)

### Completed
- ✔ Network repository  
- ✔ Per‑user vs shared mode  
- ✔ Multi‑tab editor  
- ✔ VS Code‑style theme  
- ✔ Line numbers  
- ✔ Word‑occurrence highlight  
- ✔ Zoom system  
- ✔ Indent/unindent  
- ✔ Persistent namespace  
- ✔ Console output  
- ✔ Status light  
- ✔ Backup system  

### Planned
- ☐ Script rename / duplicate / delete  
- ☐ Execution history panel  
- ☐ Variable inspector panel  
- ☐ Console filtering modes  
- ☐ Help / shortcuts tab  
- ☐ Script templates  
- ☐ Snippet library  
- ☐ Git integration  
- ☐ Per‑user settings  

---

## 📜 Changelog

### v0.12
- Major UI overhaul  
- Multi‑tab support  
- VS Code‑style theme  
- Word‑occurrence + current line highlight  
- Zoom system  
- Improved console  
- Backup system rewrite  

### v0.11
- Modular refactor  
- Basic multi‑tab  
- Improved repository handling  
- Save + backup system  
- Console redirection  

### v0.9
- Initial public beta  
- Single‑tab editor  
- Basic execution  

---





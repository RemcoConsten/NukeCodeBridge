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

## 💡 How I Built This: An Artist’s Perspective

I am an artist, not a full-time developer. Like many people in production, I often have ideas for tools that could make our lives easier, and while I know how to move around within Python, I often hit that coding wall.

This tool was an experiment to see if I could use AI as a technical assistant to bring a creative idea to life. And yes, I also used AI to help me write this README to save time. Some of you might find that lazy; I’m starting to find it a way to spend my precious time on something else.

**The Director Workflow:** Instead of writing every line of code from scratch, I acted more like a director.  
**The Concept:** I knew I wanted a way to share Nuke code snippets quickly across the studio without digging through folders.  
**The AI Collaboration:** I used AI to do the heavy lifting of building the interface. I described how I wanted the UI to react and how the list should behave, and the AI provided the building blocks.  
**Problem Solving:** When things broke, I worked with the AI to troubleshoot, testing different versions until it worked perfectly inside the Nuke environment.  
**Why I’m Sharing This:** I wanted to be open about using AI because I think it’s a game-changer for artists. It allows those of us who speak VFX but maybe do not speak Python fluently to build professional-grade tools.

---

## 🚀 What’s New Since v0.9

### **v0.12**
- Full **VS Code Dark+ themed editor**
- **Multi‑tab editing**
- **Line numbers** with custom gutter
- **Current line highlight**
- **Word‑occurrence highlighting**
- **Zoom system** (Ctrl+Wheel, Ctrl+±, Ctrl+0)
- **Indent/unindent** (Tab / Shift+Tab)
- Multi‑line indentation
- Improved **syntax highlighting**
- **Status light** (idle / running / success / error)
- Dark‑themed **console output**
- Safer **save** and **backup** behavior
- Cleaner UI layout

### **v0.11**
- Modular refactor
- Initial multi‑tab structure
- Improved repository handling
- Basic save + backup system
- Console redirection
- Persistent namespace

### **v0.9**
- First public beta
- Single‑tab editor
- Basic network loading
- Basic execution

---

Here is the updated and expanded features list, merging your original categories with all the new "Pro" features we just implemented.

## ✨ Features (v0.12)

### 📁 Network Repository & Sidebar
- **Centralized Storage:** All scripts saved to a shared network path.
- **User Sandboxing:** Toggle between your private folder and the `all_users` shared repository.
- **Live Search:** Sidebar filter to find scripts by name in real-time.
- **Dynamic Refresh:** Script list updates automatically when files are added or deleted.

### 📝 Multi‑Tab Editor
- **Unlimited Workspace:** Open as many scripts as needed.
- **Dirty State Tracking:** Tabs show an asterisk (`*`) when there are unsaved changes.
- **Smart Closables:** Individual close buttons for each tab.
- **Persistent Metadata:** Each tab tracks its own unique file path.

### 🎨 VS Code‑Style Editing
- **Dark+ Professional Theme:** High-contrast syntax highlighting optimized for long sessions.
- **Visual Navigation:** Line numbers, current line highlighting, and automatic word-occurrence highlighting.
- **No Line Wrapping:** Standard IDE behavior to maintain code structure.

### 🔍 Find & Replace Suite
- **Dual-Row UI:** Dedicated horizontal bars for Find and Replace functionality.
- **Bi-Directional Search:** Navigate through code with "Next" and "Prev" controls.
- **Bulk Replacement:** "Replace All" functionality wrapped in a single Undo block.
- **Looping Logic:** Automatically wraps from the end of the script back to the start.
- **Quick Access:** Toggled via button or the standard `Ctrl+F` shortcut.

### 🔧 Editing & Navigation Tools
- **Python-Standard Indent:** 4-space indentation with multi-line support.
- **Smart Unindent:** `Shift + Tab` to move blocks left.
- **Zoom Controls:** `Ctrl + Mouse Wheel` or `Ctrl + 0` to reset font size to 10pt.
- **Dedent Execution:** Automatically dedents highlighted snippets before running.

### ▶️ Execution Engine
- **Persistent Namespace:** Variables stay in memory between runs (no more re-importing).
- **Hardened Execution:** Captures all `stdout`, `stderr`, and full Python tracebacks.
- **Status Light System:** - ● **Grey:** Idle
  - ● **Yellow:** Busy (Executing)
  - ● **Green:** Success
  - ● **Red:** Error (Check Console)

### 🖥 Console & History Panel
- **Smart Filters:** Toggle between "All", "Errors Only", and "Actions/Info" to clean up noise.
- **Execution History:** Live log of every run. Double-click any entry to restore that snippet.
- **Variable Explorer:** View every variable currently living in your bridge's session memory.

### 💾 Save & Backup System
- **Binary Hardened Saving:** Saves in `wb` mode to prevent character mangling (e.g., brackets changing).
- **Auto-Backup:** Creates timestamped `.bak` files in a hidden `_backups` folder on every save.
- **Version Control:** Automatically keeps the last 3 versions of every script.

### 🚀 Nuke Integration
- **Universal Shortcut Layer:** Custom logic ensures `Ctrl+S`, `Ctrl+F`, and `Enter` work in both Nuke 15 (PySide2) and Nuke 17 (PySide6).
- **Native UI Feel:** Built to dock and integrate seamlessly within the Nuke interface.
---

## ⚙️ Configuration

At the top of `nuke_code_bridge.py`:

```
BASE_SHARED_PATH = r"X:\\your_shared_folder\SharedNukeScripts"
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
BASE_SHARED_PATH = r"X:\\your_shared_folder\SharedNukeScripts"
```
---

## 🧭 Usage

1. Open Nuke  
2. Go to **Scripts → NukeCodeBridge**  
3. Select a script or use “Untitled”  
4. Edit your Python code  
5. Save / Save As  
6. Run the code  
7. View output in the console  

---

---

## 🗺 Roadmap (Updated)

### Completed
- ✔ Network repository  
- ✔ Per‑user/shared mode  
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
- ☐ Variable inspector  
- ☐ Console filtering  
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
- Word‑occurrence + line highlight  
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

## 📌 Requirements

- **Foundry Nuke:** 13.0 or newer (Tested on Nuke 15)  
- **Python:** 3.7+ (Standard with Nuke 13+)  
- **Permissions:** Read/Write access to `BASE_SHARED_PATH`

---

## 🔒 Security & Usage

- **Trust:** Only execute scripts from trusted team members.  
- **Caution:** This tool uses Python’s `exec()` — just like Nuke’s Script Editor.  
  Executing unverified code can cause crashes or data loss.  
- **Permissions:** Ensure the shared directory has correct read/write access.  
- **Beta Software:** Always back up critical scripts.

---

## 🤝 Contributing

Contributions, discussions, and ideas are welcome!  
Submit Pull Requests or open Issues — especially if you are testing on Linux or macOS.

---

## 🗺️ Roadmap at a Glance

We are currently in **Phase 1 (Stability)**.  
Upcoming milestones:

- **Safety First:** Automatic `.bak` backups and namespace isolation  
- **Organization:** Tagging system and studio “read‑only” protection  
- **Insights:** Integrated console for tracebacks and deep search  

📂 *Full technical roadmap coming soon*

---

## 👨‍💻 Created by Remco Consten  
VFX Artist & Pipeline Enthusiast
<a
href="https://www.linkedin.com/in/remcoconsten/" target="_blank">LinkedIn
</a> 

---







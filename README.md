# NukeCodeBridge

**NukeCodeBridge v0.5 beta** — Remco Consten

A lightweight, network-ready mini-IDE for Foundry's Nuke. It provides a centralized, searchable repository for Python scripts that lives on a shared studio network drive. No more copying and pasting scripts between artists — everyone can write, save, run, and share tools directly inside Nuke.

## ✨ Features

- **Per-User Network Storage** (default): Each user gets their own folder on the shared drive for personal scripts.
- **Smart Code Editor**: Python syntax highlighting, line numbers, tab-to-4-spaces, smart auto-indent on colon, and Ctrl+Wheel zoom.
- **Unsaved Changes Protection**: Warns before closing or switching if you have unsaved work.
- **Flexible Execution**: Run the full script or just the selected lines.
- **Live Search**: Real-time filtering of scripts.
- **Context Menu**: Right-click any script to Run, Rename, Delete, or Copy its full network path.
- **Cross-Platform**: Works on Windows and Linux with proper path handling.
- **Cross-Version Compatible**: Automatically supports PySide2 (Nuke 13 and earlier) and PySide6 (Nuke 14+).

## 🚀 Installation

### Step 1: Prepare the Shared Location (Do this once)

1. Choose or create a central network folder that all Nuke users can read/write to.  
   Example paths:
   - Windows: `\\server\share\SharedNukeScripts`
   - Linux: `/mnt/studio/SharedNukeScripts`

2. Place the `NukeCodeBridge.py` file on the network share or in your studio tools directory.

### Step 2: Configure the Script

Open `NukeCodeBridge.py` and update the base path at the top:

```python
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"   # ← Change this to your studio path

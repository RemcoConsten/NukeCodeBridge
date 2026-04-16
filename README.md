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

### Step 1: Prepare the Shared Location

1. Choose or create a central network folder that all Nuke users can read/write to.  
   Example paths:
   - Windows: `\\server\share\SharedNukeScripts`
   - Linux: `/mnt/studio/SharedNukeScripts`

2. Place the `NukeCodeBridge.py` file inside a tools directory (for example: `\\server\share\tools` or `Y:\StudioTools`).

### Step 2: Update `init.py`

Add or replace the content of your studio’s `init.py` with the following:

```python
import nuke
import os

# =============================================
# NukeCodeBridge v0.5 beta — Remco Consten
# Network Script Manager for Nuke
# =============================================

# <<< EDIT THIS PATH TO WHERE YOUR NukeCodeBridge.py IS LOCATED >>>
NUKE_CODE_BRIDGE_PATH = r"\\YOUR_SERVER\YOUR_SHARE\tools"   # ← CHANGE THIS

# Add the directory containing NukeCodeBridge.py to Nuke's plugin path
if os.path.exists(NUKE_CODE_BRIDGE_PATH):
    nuke.pluginAddPath(NUKE_CODE_BRIDGE_PATH)
else:
    nuke.message(f"Warning: NukeCodeBridge path not found:\n{NUKE_CODE_BRIDGE_PATH}")
```

### Step 3: Update `menu.py`

Add or replace the content of your studio’s `menu.py` with the following:

```python
import nuke

# ========================
# NukeCodeBridge Menu Entry
# ========================

def launch_nuke_code_bridge():
    """Launch NukeCodeBridge v0.5 beta"""
    try:
        import NukeCodeBridge
        NukeCodeBridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

# Add tool to the Nuke menu
nuke.menu('Nuke').addCommand(
    'Scripts/NukeCodeBridge', 
    launch_nuke_code_bridge,
    shortcut=None,                    # Change to 'Shift+C' or similar if you want a hotkey
    tooltip='NukeCodeBridge v0.5 beta - Network Script Manager'
)
```

After restarting Nuke, you should see **Scripts > NukeCodeBridge** in the top menu.

## Configuration Options

Open `NukeCodeBridge.py` and edit the base path near the top:

```python
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"   # ← Change this to your studio path
```

- **Per-user folders** (default)  
- **Single shared folder** (optional): Uncomment the two lines under the configuration section.

## Requirements

- Foundry Nuke 13 or newer
- Read/Write permissions on the shared network path for all users
- No external Python packages required

## Notes

- This is a **beta** release (v0.5). Test thoroughly in your pipeline.
- The tool uses `exec()` to run scripts — only execute code you trust.
- On Linux, ensure the network share is correctly mounted with proper permissions.

---

**NukeCodeBridge v0.5 beta** — Remco Consten

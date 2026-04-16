
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
- **Cross-Platform**: Works on Windows and Linux (and macOS) with proper path handling.
- **Cross-Version Compatible**: Automatically supports PySide2 (Nuke 13 and earlier) and PySide6 (Nuke 14+).

## 🚀 Installation

### Step 1: Prepare the Shared Location (Do this once)

1. Choose or create a central network folder that all Nuke users can read/write to.  
   Example paths:
   - Windows: `\\server\share\SharedNukeScripts`
   - Linux: `/mnt/studio/SharedNukeScripts`

2. Save the `nuke_code_bridge.py` file (or whatever you name it) somewhere accessible, ideally on the same network share or in a studio tools directory.

### Step 2: Configure the Script

Open the script and edit the configuration section at the top:

```python
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"   # Change this!
```

- **Per-user folders** (default) → Each artist gets their own subfolder automatically.
- **Single shared folder** (optional, more secure/collaborative) → Uncomment the two lines in the config section to force everything into one common "Shared" folder.

### Step 3: Load in Nuke

Add one of the following to your `menu.py` (or `init.py`) so the tool appears in the Nuke menu:

```python
import nuke

def launch_nuke_code_bridge():
    import nuke_code_bridge
    nuke_code_bridge.start_nuke_code_bridge()

nuke.menu('Nuke').addCommand('Scripts/NukeCodeBridge', launch_nuke_code_bridge)
```

Alternatively, you can run it manually from the Script Editor:

```python
import nuke_code_bridge
nuke_code_bridge.start_nuke_code_bridge()
```

## Configuration Options

At the top of the script you can easily switch modes:

- **Per-user mode** (recommended default): Every user has a personal folder.
- **Single-folder mode**: Uncomment the lines to use one common folder for the whole team (better for strict permission environments).

The tool will automatically create folders as needed and includes safe fallbacks for restricted environments.

## Requirements

- Foundry Nuke 13 or newer
- Read/Write access to the shared network path for all users
- No additional Python packages required

## Notes

- This is a **beta** tool (v0.5). Test thoroughly in your studio environment.
- `exec()` is used to run scripts — only run code you trust.
- On Linux, ensure the network share is properly mounted with correct permissions.

---

Made with ❤️ for the Nuke community.

Feel free to contribute improvements or report issues!
```

This README is now clean, professional, generic, and reflects all the latest updates (name change, subtle credit, per-user default, cross-platform support, etc.).

Would you like me to add sections for "Known Limitations", "Future Plans", or a simple screenshot placeholder? Just let me know!

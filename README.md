# NukeCodeBridge

**NukeCodeBridge v0.5 beta**

A simple tool that lets you save, organize, and run Python scripts directly inside Nuke using a shared network folder.  
No more copying scripts around — everyone in the studio can access the same tools easily.

## ✨ Features

- Save scripts to a shared location (one folder per user by default)
- Built-in code editor with line numbers, syntax highlighting, and auto-indent
- Run scripts or just selected parts of code
- Search and right-click menu (Run, Rename, Delete, Copy path)
- Works on both Windows and Linux
- Supports Nuke 13 and newer versions

## 🚀 Easy Installation (Step-by-step for beginners)

### Step 1: Prepare the folders

1. Create two folders:
   - One for scripts: e.g. `\\server\share\SharedNukeScripts`
   - One for tools: e.g. `\\server\share\tools`

   **If you are working alone or in a small studio**, you can simply create these folders on your local drive (e.g. `C:\NukeTools`).

   **Tip:** Use full network paths like `\\server\share\...` instead of mapped drive letters like `Y:\` — this works better on all computers.

2. Put the file **`nuke_code_bridge.py`** into the **tools** folder.

### Step 2: Update `init.py`

Open or create the studio’s `init.py` file and add this code:

```python
import nuke
import os

# NukeCodeBridge v0.5 beta
NUKE_CODE_BRIDGE_PATH = r"\\YOUR_SERVER\YOUR_SHARE\tools"   # ← CHANGE THIS to the tools folder

if os.path.exists(NUKE_CODE_BRIDGE_PATH):
    nuke.pluginAddPath(NUKE_CODE_BRIDGE_PATH)
else:
    nuke.message(f"Warning: NukeCodeBridge path not found:\n{NUKE_CODE_BRIDGE_PATH}")
```

### Step 3: Update `menu.py`

Open or create the studio’s `menu.py` file and add this code:

```python
import nuke

def launch_nuke_code_bridge():
    """Launch NukeCodeBridge v0.5 beta"""
    try:
        import nuke_code_bridge
        nuke_code_bridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

nuke.menu('Nuke').addCommand(
    'Scripts/NukeCodeBridge', 
    launch_nuke_code_bridge,
    tooltip='Open NukeCodeBridge - Network Script Manager'
)
```

Restart Nuke. You should now see **Scripts > NukeCodeBridge** in the top menu.

## How to Configure

Open **`nuke_code_bridge.py`** and change this line to point to your shared scripts folder:

```python
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"   # ← Change this!
```

- Leave it as-is for **per-user folders** (recommended for most studios).
- To use **one shared folder** for everyone, uncomment the two lines right below it.

## Requirements

- Nuke 13 or newer
- Read/write access to the folders you created
- No extra software needed

## Notes

- This is an early version (v0.5). Feel free to try it out and give feedback!
- **Security**: The tool uses `exec()` to run scripts. A confirmation dialog will always ask before running any code.
- Only run scripts from people you trust.
- **Permissions**: Make sure users can read and write to the shared folder.
- **Linux users**: The network share must be properly mounted with read/write rights.
